class HitomiGalleryInfoModel:
    def __init__(
        self,
        language_localname,
        language,
        date,
        files,
        tags,
        japanese_title,
        title,
        galleryid,
        type,
    ):
        self.language_localname = language_localname
        self.language = language
        self.date = date
        self.files = files
        self.tags = tags
        self.japanese_title = japanese_title
        self.title = title
        self.galleryid = galleryid
        self.type = type

    @classmethod
    def parse_galleryinfo(cls, galleryinfo_json):
        return cls(
            galleryinfo_json.get("language_localname"),
            galleryinfo_json.get("language"),
            galleryinfo_json.get("date"),
            galleryinfo_json.get("files"),
            galleryinfo_json.get("tags"),
            galleryinfo_json.get("japanese_title"),
            galleryinfo_json.get("title"),
            galleryinfo_json.get("id"),
            galleryinfo_json.get("type"),
        )