const Delivery = require('../models/Delivery');
const Vehicle = require('../models/Vehicle');

const generateDeliveryNumber = () => {
  const d = new Date();
  const dateStr = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`;
  const rand = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `SVL-${dateStr}-${rand}`;
};

const getAllDeliveries = async (req, res) => {
  try {
    const deliveries = await Delivery.find()
      .populate('vehicle_id', 'vehicle_number driver_name driver_phone')
      .sort({ createdAt: -1 });
    res.json({ success: true, data: deliveries, count: deliveries.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getDeliveryById = async (req, res) => {
  try {
    const delivery = await Delivery.findById(req.params.id)
      .populate('vehicle_id', 'vehicle_number driver_name driver_phone capacity')
      .populate('items.stock_id');

    if (!delivery)
      return res.status(404).json({ success: false, message: 'Delivery not found' });

    res.json({ success: true, data: delivery });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createDelivery = async (req, res) => {
  try {
    const { vehicle_id, destination, destination_market, scheduled_date, driver_notes, items } = req.body;
    if (!vehicle_id || !destination)
      return res.status(400).json({ success: false, message: 'Vehicle and destination are required' });

    let total_quantity = 0;
    let total_value = 0;
    const deliveryItems = [];

    if (items && items.length > 0) {
      items.forEach(item => {
        total_quantity += parseFloat(item.quantity);
        total_value += parseFloat(item.quantity) * parseFloat(item.price_per_unit);
        deliveryItems.push({
          stock_id: item.stock_id,
          quantity: item.quantity,
          price_per_unit: item.price_per_unit,
          selling_price: item.selling_price || item.price_per_unit
        });
      });
    }

    const delivery = await Delivery.create({
      delivery_number: generateDeliveryNumber(),
      vehicle_id,
      destination,
      destination_market: destination_market || '',
      total_quantity,
      total_value,
      scheduled_date: scheduled_date || new Date(),
      driver_notes: driver_notes || '',
      items: deliveryItems
    });

    // Mark vehicle as in-transit
    await Vehicle.findByIdAndUpdate(vehicle_id, { status: 'in-transit' });

    res.status(201).json({ success: true, message: 'Delivery created successfully', data: delivery });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateDeliveryStatus = async (req, res) => {
  try {
    const { status, delivered_date, driver_notes } = req.body;
    const validStatuses = ['pending', 'in-transit', 'delivered', 'cancelled'];
    if (!validStatuses.includes(status))
      return res.status(400).json({ success: false, message: 'Invalid status' });

    const updateData = { status, driver_notes: driver_notes || '' };
    if (status === 'delivered') updateData.delivered_date = delivered_date || new Date();

    const delivery = await Delivery.findByIdAndUpdate(req.params.id, updateData, { new: true });
    if (!delivery)
      return res.status(404).json({ success: false, message: 'Delivery not found' });

    // Free the vehicle if done
    if (status === 'delivered' || status === 'cancelled') {
      await Vehicle.findByIdAndUpdate(delivery.vehicle_id, { status: 'available' });
    }

    res.json({ success: true, message: 'Delivery status updated', data: delivery });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteDelivery = async (req, res) => {
  try {
    // Items are embedded, so deleting the delivery removes them automatically
    const delivery = await Delivery.findByIdAndDelete(req.params.id);
    if (!delivery)
      return res.status(404).json({ success: false, message: 'Delivery not found' });
    res.json({ success: true, message: 'Delivery deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllDeliveries, getDeliveryById, createDelivery, updateDeliveryStatus, deleteDelivery };
