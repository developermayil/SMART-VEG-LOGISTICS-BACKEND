const Vehicle = require('../models/Vehicle');
const Delivery = require('../models/Delivery');

const getAllVehicles = async (req, res) => {
  try {
    const vehicles = await Vehicle.find().sort({ createdAt: -1 }).lean();

    const stats = await Delivery.aggregate([
      { $group: {
          _id: '$vehicle_id',
          total_deliveries: { $sum: 1 },
          completed_deliveries: { $sum: { $cond: [{ $eq: ['$status', 'delivered'] }, 1, 0] } }
      }}
    ]);
    const statsMap = Object.fromEntries(stats.map(s => [String(s._id), s]));

    const data = vehicles.map(v => ({
      ...v,
      total_deliveries: statsMap[String(v._id)]?.total_deliveries || 0,
      completed_deliveries: statsMap[String(v._id)]?.completed_deliveries || 0
    }));

    res.json({ success: true, data, count: data.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getVehicleById = async (req, res) => {
  try {
    const vehicle = await Vehicle.findById(req.params.id);
    if (!vehicle)
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    res.json({ success: true, data: vehicle });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createVehicle = async (req, res) => {
  try {
    const { vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity } = req.body;
    if (!vehicle_number || !driver_name || !driver_phone || !capacity)
      return res.status(400).json({ success: false, message: 'Vehicle number, driver name, phone, and capacity are required' });

    const vehicle = await Vehicle.create({ vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity });
    res.status(201).json({ success: true, message: 'Vehicle added successfully', data: vehicle });
  } catch (err) {
    if (err.code === 11000)
      return res.status(409).json({ success: false, message: 'Vehicle number already exists' });
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateVehicle = async (req, res) => {
  try {
    const { vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity, status } = req.body;
    const vehicle = await Vehicle.findByIdAndUpdate(
      req.params.id,
      { vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity, status },
      { new: true, runValidators: true }
    );
    if (!vehicle)
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    res.json({ success: true, message: 'Vehicle updated successfully', data: vehicle });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteVehicle = async (req, res) => {
  try {
    const vehicle = await Vehicle.findByIdAndDelete(req.params.id);
    if (!vehicle)
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    res.json({ success: true, message: 'Vehicle deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getAvailableVehicles = async (req, res) => {
  try {
    const vehicles = await Vehicle.find({ status: 'available' }).sort({ capacity: -1 });
    res.json({ success: true, data: vehicles });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllVehicles, getVehicleById, createVehicle, updateVehicle, deleteVehicle, getAvailableVehicles };
