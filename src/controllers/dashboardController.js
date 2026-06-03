const Stock = require('../models/Stock');
const Farmer = require('../models/Farmer');
const Vehicle = require('../models/Vehicle');
const Delivery = require('../models/Delivery');

const getDashboardStats = async (req, res) => {
  try {
    const [stockAgg, totalFarmers, vehicleAgg, deliveryAgg, recentDeliveries, stockByVeg] = await Promise.all([
      Stock.aggregate([
        { $group: {
            _id: null,
            total_items: { $sum: 1 },
            total_quantity: { $sum: '$quantity' },
            total_stock_value: { $sum: { $multiply: ['$quantity', '$price_per_unit'] } }
        }}
      ]),
      Farmer.countDocuments(),
      Vehicle.aggregate([
        { $group: {
            _id: null,
            total_vehicles: { $sum: 1 },
            available: { $sum: { $cond: [{ $eq: ['$status', 'available'] }, 1, 0] } },
            in_transit: { $sum: { $cond: [{ $eq: ['$status', 'in-transit'] }, 1, 0] } }
        }}
      ]),
      Delivery.aggregate([
        { $group: {
            _id: null,
            total_deliveries: { $sum: 1 },
            completed: { $sum: { $cond: [{ $eq: ['$status', 'delivered'] }, 1, 0] } },
            active: { $sum: { $cond: [{ $eq: ['$status', 'in-transit'] }, 1, 0] } },
            revenue: { $sum: { $cond: [{ $eq: ['$status', 'delivered'] }, '$total_value', 0] } }
        }}
      ]),
      Delivery.find()
        .populate('vehicle_id', 'vehicle_number driver_name')
        .sort({ createdAt: -1 })
        .limit(5)
        .select('delivery_number destination status total_value scheduled_date'),
      Stock.aggregate([
        { $group: {
            _id: '$vegetable',
            total_quantity: { $sum: '$quantity' },
            avg_price: { $avg: '$price_per_unit' }
        }},
        { $project: { vegetable: '$_id', total_quantity: 1, avg_price: 1, _id: 0 } },
        { $sort: { total_quantity: -1 } }
      ])
    ]);

    res.json({
      success: true,
      data: {
        stocks: stockAgg[0] || { total_items: 0, total_quantity: 0, total_stock_value: 0 },
        farmers: { total_farmers: totalFarmers },
        vehicles: vehicleAgg[0] || { total_vehicles: 0, available: 0, in_transit: 0 },
        deliveries: deliveryAgg[0] || { total_deliveries: 0, completed: 0, active: 0, revenue: 0 },
        recent_deliveries: recentDeliveries,
        stock_by_vegetable: stockByVeg
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getDashboardStats };
