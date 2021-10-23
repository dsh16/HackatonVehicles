module.exports = {
  HOST: "localhost",
  // PORT: "3006",
  USER: "root",
  // PASSWORD: "fsds",
  PASSWORD: "",
  DB: "hackaton",
  dialect: "mysql",
  pool: {
    max: 5,
    min: 0,
    acquire: 30000,
    idle: 10000
  }
};
