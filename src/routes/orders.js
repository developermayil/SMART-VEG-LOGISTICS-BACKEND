const express = require('express');
const router = express.Router();
const Order = require('../models/Order');
const Customer = require('../models/Customer');

// Get all orders
router.get('/', async (req, res) => {
  try {
    const orders = await Order.find()
      .populate('customer_id', 'name phone address')
      .sort({ created_date: -1 });
    
    // Transform data for frontend
    const transformedOrders = orders.map(order => ({
      _id: order._id,
      order_number: order.order_number,
      customer_id: order.customer_id._id,
      customer_name: order.customer_id.name,
      customer_phone: order.customer_id.phone,
      items: order.items,
      total_amount: order.total_amount,
      status: order.status,
      notes: order.notes,
      created_date: order.created_date
    }));
    
    res.json({ success: true, data: transformedOrders });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get single order
router.get('/:id', async (req, res) => {
  try {
    const order = await Order.findById(req.params.id).populate('customer_id', 'name phone address');
    if (!order) {
      return res.status(404).json({ success: false, message: 'Order not found' });
    }
    res.json({ success: true, data: order });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Create order
router.post('/', async (req, res) => {
  try {
    const { customer_id, items, total_amount, status, notes, created_date } = req.body;
    
    // Verify customer exists
    const customer = await Customer.findById(customer_id);
    if (!customer) {
      return res.status(404).json({ success: false, message: 'Customer not found' });
    }
    
    const order = new Order({
      customer_id,
      items,
      total_amount: parseFloat(total_amount),
      status: status || 'pending',
      notes: notes || '',
      created_date: created_date ? new Date(created_date) : new Date()
    });
    
    await order.save();
    
    // Populate customer data for response
    await order.populate('customer_id', 'name phone');
    
    res.json({ success: true, data: order });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Update order
router.put('/:id', async (req, res) => {
  try {
    const { customer_id, items, total_amount, status, notes, created_date } = req.body;
    
    const order = await Order.findByIdAndUpdate(
      req.params.id,
      {
        customer_id,
        items,
        total_amount: parseFloat(total_amount),
        status,
        notes,
        created_date: created_date ? new Date(created_date) : undefined,
        updated_at: Date.now()
      },
      { new: true, runValidators: true }
    ).populate('customer_id', 'name phone');
    
    if (!order) {
      return res.status(404).json({ success: false, message: 'Order not found' });
    }
    
    res.json({ success: true, data: order });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Delete order
router.delete('/:id', async (req, res) => {
  try {
    const order = await Order.findByIdAndDelete(req.params.id);
    if (!order) {
      return res.status(404).json({ success: false, message: 'Order not found' });
    }
    res.json({ success: true, message: 'Order deleted successfully' });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get orders by customer
router.get('/customer/:customerId', async (req, res) => {
  try {
    const orders = await Order.find({ customer_id: req.params.customerId })
      .sort({ created_date: -1 });
    res.json({ success: true, data: orders });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Update order status
router.patch('/:id/status', async (req, res) => {
  try {
    const { status } = req.body;
    const order = await Order.findByIdAndUpdate(
      req.params.id,
      { status, updated_at: Date.now() },
      { new: true }
    );
    if (!order) {
      return res.status(404).json({ success: false, message: 'Order not found' });
    }
    res.json({ success: true, data: order });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

module.exports = router;