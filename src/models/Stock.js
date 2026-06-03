const mongoose = require('mongoose');

const stockSchema = new mongoose.Schema({
  vegetable:      { type: String, required: true },
  quantity:       { type: Number, required: true },
  unit:           { type: String, default: 'kg' },
  price_per_unit: { type: Number, required: true },
  farmer_id:      { type: mongoose.Schema.Types.ObjectId, ref: 'Farmer', default: null },
  purchase_date:  { type: Date, default: Date.now },
  notes:          { type: String, default: '' }
}, { timestamps: true });

module.exports = mongoose.model('Stock', stockSchema);
