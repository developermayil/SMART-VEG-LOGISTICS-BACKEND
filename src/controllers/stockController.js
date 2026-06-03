const Stock = require('../models/Stock');

const getAllStocks = async (req, res) => {
  try {
    const stocks = await Stock.find()
      .populate('farmer_id', 'name village')
      .sort({ createdAt: -1 });

    // Normalize farmer fields to match old SQL response shape
    const data = stocks.map(s => {
      const obj = s.toObject();
      obj.farmer_name = obj.farmer_id?.name || null;
      obj.farmer_village = obj.farmer_id?.village || null;
      return obj;
    });

    res.json({ success: true, data, count: data.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getStockById = async (req, res) => {
  try {
    const stock = await Stock.findById(req.params.id).populate('farmer_id', 'name village');
    if (!stock)
      return res.status(404).json({ success: false, message: 'Stock not found' });

    const obj = stock.toObject();
    obj.farmer_name = obj.farmer_id?.name || null;
    obj.farmer_village = obj.farmer_id?.village || null;
    res.json({ success: true, data: obj });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createStock = async (req, res) => {
  try {
    const { vegetable, quantity, unit, price_per_unit, farmer_id, purchase_date, notes } = req.body;
    if (!vegetable || !quantity || !price_per_unit)
      return res.status(400).json({ success: false, message: 'Vegetable, quantity, and price are required' });

    const stock = await Stock.create({ vegetable, quantity, unit, price_per_unit, farmer_id: farmer_id || null, purchase_date, notes });
    res.status(201).json({ success: true, message: 'Stock added successfully', data: stock });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateStock = async (req, res) => {
  try {
    const { vegetable, quantity, unit, price_per_unit, farmer_id, purchase_date, notes } = req.body;
    const stock = await Stock.findByIdAndUpdate(
      req.params.id,
      { vegetable, quantity, unit, price_per_unit, farmer_id: farmer_id || null, purchase_date, notes },
      { new: true, runValidators: true }
    );
    if (!stock)
      return res.status(404).json({ success: false, message: 'Stock not found' });
    res.json({ success: true, message: 'Stock updated successfully', data: stock });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteStock = async (req, res) => {
  try {
    const stock = await Stock.findByIdAndDelete(req.params.id);
    if (!stock)
      return res.status(404).json({ success: false, message: 'Stock not found' });
    res.json({ success: true, message: 'Stock deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getStockSummary = async (req, res) => {
  try {
    const result = await Stock.aggregate([
      { $group: {
          _id: null,
          total_items: { $sum: 1 },
          total_quantity: { $sum: '$quantity' },
          total_value: { $sum: { $multiply: ['$quantity', '$price_per_unit'] } },
          unique_vegetables: { $addToSet: '$vegetable' }
      }},
      { $project: { _id: 0, total_items: 1, total_quantity: 1, total_value: 1, unique_vegetables: { $size: '$unique_vegetables' } } }
    ]);
    res.json({ success: true, data: result[0] || { total_items: 0, total_quantity: 0, total_value: 0, unique_vegetables: 0 } });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllStocks, getStockById, createStock, updateStock, deleteStock, getStockSummary };
