var multer = require("multer");

var fileFilterImage = (req, file, cb) => {
    const allowedTypes = ["image/jpeg", "image/jpg", "image/png"];
    if (!allowedTypes.includes(file.mimetype)) {
        const error = new Error("Incorrect file");
        error.code = "INCORRECT_FILETYPE";
        return cb(error, false)
    }
    cb(null, true);
}

var storageImage = multer.diskStorage({
    destination: function (req, file, cb) {
      cb(null, 'public/avatars')
    },
    filename: function (req, file, cb) {
      cb(null, Date.now() + '-' + file.originalname)
    }
})

var uploadImage = multer({
    storage : storageImage,
    fileFilter: fileFilterImage,
});

module.exports = function (req, res, next) {
    try {
        uploadImage.single('file')
        next();
    } catch (e) {
        return next(ApiError.BadRequest('Валидация не прошла'));
    }
};
