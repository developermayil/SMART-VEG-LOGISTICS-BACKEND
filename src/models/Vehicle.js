const mongoose = require('mongoose');

const vehicleSchema = new mongoose.Schema({
  vehicle_number: { type: String, required: true, unique: true },
  vehicle_type:   { type: String, default: 'Truck' },
  driver_name:    { type: String, required: true },
  driver_phone:   { type: String, required: true },
  driver_license: { type: String, default: '' },
  capacity:       { type: Number, required: true },
  status:         { type: String, default: 'available', enum: ['available', 'in-transit', 'maintenance'] }
}, { timestamps: true });

module.exports = mongoose.model('Vehicle', vehicleSchema);
