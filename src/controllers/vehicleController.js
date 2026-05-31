const { getPool, sql } = require('../db/database');

const getAllVehicles = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query(`
      SELECT v.*,
        COUNT(d.id) AS total_deliveries,
        SUM(CASE WHEN d.status = 'delivered' THEN 1 ELSE 0 END) AS completed_deliveries
      FROM Vehicles v
      LEFT JOIN Deliveries d ON v.id = d.vehicle_id
      GROUP BY v.id, v.vehicle_number, v.vehicle_type, v.driver_name, v.driver_phone,
               v.driver_license, v.capacity, v.status, v.created_at, v.updated_at
      ORDER BY v.created_at DESC
    `);
    res.json({ success: true, data: result.recordset, count: result.recordset.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getVehicleById = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('SELECT * FROM Vehicles WHERE id = @id');
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    }
    res.json({ success: true, data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createVehicle = async (req, res) => {
  try {
    const { vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity } = req.body;
    if (!vehicle_number || !driver_name || !driver_phone || !capacity) {
      return res.status(400).json({ success: false, message: 'Vehicle number, driver name, phone, and capacity are required' });
    }
    const pool = await getPool();
    const result = await pool.request()
      .input('vehicle_number', sql.NVarChar, vehicle_number)
      .input('vehicle_type', sql.NVarChar, vehicle_type || 'Truck')
      .input('driver_name', sql.NVarChar, driver_name)
      .input('driver_phone', sql.NVarChar, driver_phone)
      .input('driver_license', sql.NVarChar, driver_license || '')
      .input('capacity', sql.Decimal(10, 2), capacity)
      .query(`
        INSERT INTO Vehicles (vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity)
        OUTPUT INSERTED.*
        VALUES (@vehicle_number, @vehicle_type, @driver_name, @driver_phone, @driver_license, @capacity)
      `);
    res.status(201).json({ success: true, message: 'Vehicle added successfully', data: result.recordset[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateVehicle = async (req, res) => {
  try {
    const { vehicle_number, vehicle_type, driver_name, driver_phone, driver_license, capacity, status } = req.body;
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .input('vehicle_number', sql.NVarChar, vehicle_number)
      .input('vehicle_type', sql.NVarChar, vehicle_type)
      .input('driver_name', sql.NVarChar, driver_name)
      .input('driver_phone', sql.NVarChar, driver_phone)
      .input('driver_license', sql.NVarChar, driver_license)
      .input('capacity', sql.Decimal(10, 2), capacity)
      .input('status', sql.NVarChar, status || 'available')
      .query(`
        UPDATE Vehicles SET vehicle_number=@vehicle_number, vehicle_type=@vehicle_type,
          driver_name=@driver_name, driver_phone=@driver_phone, driver_license=@driver_license,
          capacity=@capacity, status=@status, updated_at=GETDATE()
        OUTPUT INSERTED.*
        WHERE id = @id
      `);
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    }
    res.json({ success: true, message: 'Vehicle updated successfully', data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteVehicle = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('DELETE FROM Vehicles OUTPUT DELETED.id WHERE id = @id');
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Vehicle not found' });
    }
    res.json({ success: true, message: 'Vehicle deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getAvailableVehicles = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .query("SELECT * FROM Vehicles WHERE status = 'available' ORDER BY capacity DESC");
    res.json({ success: true, data: result.recordset });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllVehicles, getVehicleById, createVehicle, updateVehicle, deleteVehicle, getAvailableVehicles };
