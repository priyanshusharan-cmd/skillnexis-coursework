const mongoose = require('mongoose');
const { createApp } = require('./app');

const { MONGO_URI = 'mongodb://127.0.0.1:27017/sn_mern', JWT_SECRET, PORT = 4000, CORS_ORIGIN } = process.env;

mongoose
  .connect(MONGO_URI)
  .then(() => {
    createApp({ jwtSecret: JWT_SECRET, corsOrigin: CORS_ORIGIN }).listen(PORT, () => console.log(`API listening on ${PORT}`));
  })
  .catch(err => {
    console.error(err.message);
    process.exit(1);
  });
