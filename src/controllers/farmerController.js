const Farmer = require('../models/Farmer');
const Stock = require('../models/Stock');

const getAllFarmers = async (req, res) => {
  try {
    const farmers = await Farmer.find().sort({ createdAt: -1 }).lean();

    // Aggregate supply stats per farmer
    const stats = await Stock.aggregate([
      { $group: {
          _id: '$farmer_id',
          total_supplies: { $sum: 1 },
          total_quantity_supplied: { $sum: '$quantity' },
          total_value: { $sum: { $multiply: ['$quantity', '$price_per_unit'] } }
      }}
    ]);
    const statsMap = Object.fromEntries(stats.map(s => [String(s._id), s]));

    const data = farmers.map(f => ({
      ...f,
      total_supplies: statsMap[String(f._id)]?.total_supplies || 0,
      total_quantity_supplied: statsMap[String(f._id)]?.total_quantity_supplied || 0,
      total_value: statsMap[String(f._id)]?.total_value || 0
    }));

    res.json({ success: true, data, count: data.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getFarmerById = async (req, res) => {
  try {
    const farmer = await Farmer.findById(req.params.id);
    if (!farmer)
      return res.status(404).json({ success: false, message: 'Farmer not found' });

    const supplies = await Stock.find({ farmer_id: req.params.id }).sort({ createdAt: -1 });
    res.json({ success: true, data: { ...farmer.toObject(), supplies } });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createFarmer = async (req, res) => {
  try {
    const { name, village, district, phone, alternate_phone, email, bank_account, ifsc_code } = req.body;
    if (!name || !village || !phone)
      return res.status(400).json({ success: false, message: 'Name, village, and phone are required' });

    const farmer = await Farmer.create({ name, village, district, phone, alternate_phone, email, bank_account, ifsc_code });
    res.status(201).json({ success: true, message: 'Farmer registered successfully', data: farmer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateFarmer = async (req, res) => {
  try {
    const { name, village, district, phone, alternate_phone, email, bank_account, ifsc_code } = req.body;
    const farmer = await Farmer.findByIdAndUpdate(
      req.params.id,
      { name, village, district, phone, alternate_phone, email, bank_account, ifsc_code },
      { new: true, runValidators: true }
    );
    if (!farmer)
      return res.status(404).json({ success: false, message: 'Farmer not found' });

    res.json({ success: true, message: 'Farmer updated successfully', data: farmer });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteFarmer = async (req, res) => {
  try {
    const farmer = await Farmer.findByIdAndDelete(req.params.id);
    if (!farmer)
      return res.status(404).json({ success: false, message: 'Farmer not found' });

    res.json({ success: true, message: 'Farmer deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllFarmers, getFarmerById, createFarmer, updateFarmer, deleteFarmer };
