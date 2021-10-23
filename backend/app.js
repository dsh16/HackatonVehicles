require('dotenv').config()
var express = require('express');
var path = require('path');
var cookieParser = require('cookie-parser');
var logger = require('morgan');
const cors = require('cors');
const errorMiddleware = require('./middlewares/error-middleware');
var app = express();

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(cors({
    credentials: true,
    origin: process.env.CLIENT_URL
}));

// const db = require("./models");

// db.sequelize.sync();

app.get("/", (req, res) => {
    res.json({ message: "Hello world!" });
});

require("./routes/user.routes")(app);

app.use(errorMiddleware);

module.exports = app;
