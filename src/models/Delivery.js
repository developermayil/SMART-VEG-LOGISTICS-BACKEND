const mongoose = require('mongoose');

const deliveryItemSchema = new mongoose.Schema({
  stock_id:       { type: mongoose.Schema.Types.ObjectId, ref: 'Stock', required: true },
  quantity:       { type: Number, required: true },
  price_per_unit: { type: Number, required: true },
  selling_price:  { type: Number }
}, { _id: true, timestamps: true });

const deliverySchema = new mongoose.Schema({
  delivery_number:    { type: String, required: true, unique: true },
  vehicle_id:         { type: mongoose.Schema.Types.ObjectId, ref: 'Vehicle', required: true },
  destination:        { type: String, required: true },
  destination_market: { type: String, default: '' },
  total_quantity:     { type: Number, default: 0 },
  total_value:        { type: Number, default: 0 },
  status:             { type: String, default: 'pending', enum: ['pending', 'in-transit', 'delivered', 'cancelled'] },
  scheduled_date:     { type: Date },
  delivered_date:     { type: Date },
  driver_notes:       { type: String, default: '' },
  items:              [deliveryItemSchema]
}, { timestamps: true });

module.exports = mongoose.model('Delivery', deliverySchema);
