const { getPool, sql } = require('../db/database');

const generateDeliveryNumber = () => {
  const date = new Date();
  const dateStr = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
  const rand = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `SVL-${dateStr}-${rand}`;
};

const getAllDeliveries = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query(`
      SELECT d.*, v.vehicle_number, v.driver_name, v.driver_phone
      FROM Deliveries d
      LEFT JOIN Vehicles v ON d.vehicle_id = v.id
      ORDER BY d.created_at DESC
    `);
    res.json({ success: true, data: result.recordset, count: result.recordset.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getDeliveryById = async (req, res) => {
  try {
    const pool = await getPool();
    const delivery = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query(`
        SELECT d.*, v.vehicle_number, v.driver_name, v.driver_phone, v.capacity
        FROM Deliveries d
        LEFT JOIN Vehicles v ON d.vehicle_id = v.id
        WHERE d.id = @id
      `);

    if (delivery.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Delivery not found' });
    }

    const items = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query(`
        SELECT di.*, s.vegetable, s.unit, f.name AS farmer_name
        FROM DeliveryItems di
        JOIN Stocks s ON di.stock_id = s.id
        LEFT JOIN Farmers f ON s.farmer_id = f.id
        WHERE di.delivery_id = @id
      `);

    res.json({ success: true, data: { ...delivery.recordset[0], items: items.recordset } });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createDelivery = async (req, res) => {
  try {
    const { vehicle_id, destination, destination_market, scheduled_date, driver_notes, items } = req.body;
    if (!vehicle_id || !destination) {
      return res.status(400).json({ success: false, message: 'Vehicle and destination are required' });
    }

    const delivery_number = generateDeliveryNumber();
    const pool = await getPool();

    // Calculate totals from items
    let total_quantity = 0;
    let total_value = 0;
    if (items && items.length > 0) {
      items.forEach(item => {
        total_quantity += parseFloat(item.quantity);
        total_value += parseFloat(item.quantity) * parseFloat(item.price_per_unit);
      });
    }

    const result = await pool.request()
      .input('delivery_number', sql.NVarChar, delivery_number)
      .input('vehicle_id', sql.Int, vehicle_id)
      .input('destination', sql.NVarChar, destination)
      .input('destination_market', sql.NVarChar, destination_market || '')
      .input('total_quantity', sql.Decimal(10, 2), total_quantity)
      .input('total_value', sql.Decimal(12, 2), total_value)
      .input('scheduled_date', sql.DateTime, scheduled_date || new Date())
      .input('driver_notes', sql.NVarChar, driver_notes || '')
      .query(`
        INSERT INTO Deliveries (delivery_number, vehicle_id, destination, destination_market, total_quantity, total_value, scheduled_date, driver_notes)
        OUTPUT INSERTED.*
        VALUES (@delivery_number, @vehicle_id, @destination, @destination_market, @total_quantity, @total_value, @scheduled_date, @driver_notes)
      `);

    const delivery = result.recordset[0];

    // Insert delivery items
    if (items && items.length > 0) {
      for (const item of items) {
        await pool.request()
          .input('delivery_id', sql.Int, delivery.id)
          .input('stock_id', sql.Int, item.stock_id)
          .input('quantity', sql.Decimal(10, 2), item.quantity)
          .input('price_per_unit', sql.Decimal(10, 2), item.price_per_unit)
          .input('selling_price', sql.Decimal(10, 2), item.selling_price || item.price_per_unit)
          .query(`
            INSERT INTO DeliveryItems (delivery_id, stock_id, quantity, price_per_unit, selling_price)
            VALUES (@delivery_id, @stock_id, @quantity, @price_per_unit, @selling_price)
          `);
      }
    }

    // Update vehicle status to in-transit
    await pool.request()
      .input('vehicle_id', sql.Int, vehicle_id)
      .query("UPDATE Vehicles SET status='in-transit' WHERE id=@vehicle_id");

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
    if (!validStatuses.includes(status)) {
      return res.status(400).json({ success: false, message: 'Invalid status' });
    }

    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .input('status', sql.NVarChar, status)
      .input('delivered_date', sql.DateTime, status === 'delivered' ? (delivered_date || new Date()) : null)
      .input('driver_notes', sql.NVarChar, driver_notes || '')
      .query(`
        UPDATE Deliveries
        SET status=@status, delivered_date=@delivered_date, driver_notes=@driver_notes, updated_at=GETDATE()
        OUTPUT INSERTED.*, INSERTED.vehicle_id
        WHERE id = @id
      `);

    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Delivery not found' });
    }

    // If delivered or cancelled, free the vehicle
    if (status === 'delivered' || status === 'cancelled') {
      await pool.request()
        .input('vehicle_id', sql.Int, result.recordset[0].vehicle_id)
        .query("UPDATE Vehicles SET status='available' WHERE id=@vehicle_id");
    }

    res.json({ success: true, message: 'Delivery status updated', data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteDelivery = async (req, res) => {
  try {
    const pool = await getPool();
    // Delete items first
    await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('DELETE FROM DeliveryItems WHERE delivery_id = @id');

    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('DELETE FROM Deliveries OUTPUT DELETED.id WHERE id = @id');

    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Delivery not found' });
    }
    res.json({ success: true, message: 'Delivery deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllDeliveries, getDeliveryById, createDelivery, updateDeliveryStatus, deleteDelivery };
