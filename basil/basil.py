import json
from basil.parser import HitomiGalleryInfoModel
from tortoise import Tortoise, run_async
from basil.models import *
import aiohttp
import struct


class Basil:
    def __init__(self, db_url: str, index_file: str):
        self.db_url = db_url
        self.index_file = index_file
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        self.domain = "hitomi.la"

    async def fetch_index(self, index_file):
        byte_start = (1 - 1) * 25 * 4
        byte_end = byte_start + 25 * 4 - 1

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://ltn.{self.domain}/{index_file}",
                headers={
                    "User-Agent": self.ua,
                    "Range": f"byte={byte_start}-{byte_end}",
                    "referer": f"https://{self.domain}/index-all-1.html",
                    "origin": f"http://{self.domain}",
                },
            ) as r:
                response_bytes = await r.read()

        total_items = len(response_bytes) // 4
        return struct.unpack(f">{total_items}i", bytes(response_bytes))

    async def get_galleryinfo(self, index: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://ltn.{self.domain}/galleries/{index}.js",
                headers={"referer": f"http://{self.domain}", "User-Agent": self.ua},
            ) as r:
                js_to_json = (await r.text()).replace("var galleryinfo = ", "")
                return HitomiGalleryInfoModel.parse_galleryinfo(json.loads(js_to_json))
            
    async def migration_index(self):
        await Tortoise.init(
            db_url=self.db_url,
            modules={"models": ["basil.models"]},
        )
        await Tortoise.generate_schemas()

        index_list = await self.fetch_index(self.index_file)
        total_index_list = len(index_list)
        count = 0

        for index in index_list:
            await Index.create(index_id=index)
            print(f"{index} 완료 ({count}/{total_index_list})")

    async def migration(self):
        await Tortoise.init(
            db_url=self.db_url,
            modules={"models": ["basil.models"]},
        )
        await Tortoise.generate_schemas()

        index_list = await self.fetch_index(self.index_file)
        total_index_list = len(index_list)
        count = 0
        for index in index_list:
            galleryinfo = await self.get_galleryinfo(index)

            if await GalleryInfo.get_or_none(id=galleryinfo.galleryid):
                print(f"{index} 패스됨 ({count}/{total_index_list})")
                count += 1
                continue

            galleyinfo_orm_object = await GalleryInfo.create(
                language_localname=galleryinfo.language_localname,
                language=galleryinfo.language,
                date=galleryinfo.date,
                japanese_title=galleryinfo.japanese_title,
                title=galleryinfo.title,
                id=galleryinfo.galleryid,
                type=galleryinfo.type,
            )

            if galleryinfo.files:
                file_orm_object_list = []
                for file_info in galleryinfo.files:
                    file_orm_object = File(
                        index_id=galleryinfo.galleryid,
                        width=file_info.get("width"),
                        hash=file_info.get("hash"),
                        haswebp=file_info.get("haswebp"),
                        hasavifsmalltn=file_info.get("hasavifsmalltn"),
                        name=file_info.get("name"),
                        height=file_info.get("height"),
                        hasavif=file_info.get("hasavif"),
                    )
                    await file_orm_object.save()
                    file_orm_object_list.append(file_orm_object)
                await galleyinfo_orm_object.files.add(*file_orm_object_list)

            if galleryinfo.tags:
                tag_orm_object_list = []
                for tag_info in galleryinfo.tags:
                    tag_orm_object = Tag(
                        index_id=galleryinfo.galleryid,
                        male=tag_info.get("male"),
                        female=tag_info.get("female"),
                        url=tag_info.get("url"),
                    )
                    await tag_orm_object.save()
                    tag_orm_object_list.append(tag_orm_object)

                await galleyinfo_orm_object.tags.add(*tag_orm_object_list)
            count += 1
            print(f"{index} 완료 ({count}/{total_index_list})")

    def start(self):
        run_async(self.migration())
    
    def start_index(self):
        run_async(self.migration_index())
