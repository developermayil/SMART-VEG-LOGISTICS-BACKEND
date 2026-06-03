const mongoose = require('mongoose');

const farmerSchema = new mongoose.Schema({
  name:            { type: String, required: true },
  village:         { type: String, required: true },
  district:        { type: String, default: 'Tamil Nadu' },
  phone:           { type: String, required: true },
  alternate_phone: { type: String, default: '' },
  email:           { type: String, default: '' },
  bank_account:    { type: String, default: '' },
  ifsc_code:       { type: String, default: '' }
}, { timestamps: true });

module.exports = mongoose.model('Farmer', farmerSchema);
