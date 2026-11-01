const mongoose = require('mongoose');

const noteSchema = new mongoose.Schema(
  {
    owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    title: { type: String, required: true, trim: true, maxlength: 120 },
    body: { type: String, default: '', maxlength: 10000 },
  },
  { timestamps: true }
);

module.exports = mongoose.model('Note', noteSchema);
