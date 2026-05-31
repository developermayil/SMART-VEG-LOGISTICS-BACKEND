const { getPool, sql } = require('../db/database');

const getAllFarmers = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query(`
      SELECT f.*,
        COUNT(s.id) AS total_supplies,
        COALESCE(SUM(s.quantity), 0) AS total_quantity_supplied,
        COALESCE(SUM(s.quantity * s.price_per_unit), 0) AS total_value
      FROM Farmers f
      LEFT JOIN Stocks s ON f.id = s.farmer_id
      GROUP BY f.id, f.name, f.village, f.district, f.phone, f.alternate_phone, f.email, f.bank_account, f.ifsc_code, f.created_at, f.updated_at
      ORDER BY f.created_at DESC
    `);
    res.json({ success: true, data: result.recordset, count: result.recordset.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getFarmerById = async (req, res) => {
  try {
    const pool = await getPool();
    const farmer = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('SELECT * FROM Farmers WHERE id = @id');

    if (farmer.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Farmer not found' });
    }

    const supplies = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('SELECT * FROM Stocks WHERE farmer_id = @id ORDER BY created_at DESC');

    res.json({ success: true, data: { ...farmer.recordset[0], supplies: supplies.recordset } });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createFarmer = async (req, res) => {
  try {
    const { name, village, district, phone, alternate_phone, email, bank_account, ifsc_code } = req.body;
    if (!name || !village || !phone) {
      return res.status(400).json({ success: false, message: 'Name, village, and phone are required' });
    }
    const pool = await getPool();
    const result = await pool.request()
      .input('name', sql.NVarChar, name)
      .input('village', sql.NVarChar, village)
      .input('district', sql.NVarChar, district || 'Tamil Nadu')
      .input('phone', sql.NVarChar, phone)
      .input('alternate_phone', sql.NVarChar, alternate_phone || '')
      .input('email', sql.NVarChar, email || '')
      .input('bank_account', sql.NVarChar, bank_account || '')
      .input('ifsc_code', sql.NVarChar, ifsc_code || '')
      .query(`
        INSERT INTO Farmers (name, village, district, phone, alternate_phone, email, bank_account, ifsc_code)
        OUTPUT INSERTED.*
        VALUES (@name, @village, @district, @phone, @alternate_phone, @email, @bank_account, @ifsc_code)
      `);
    res.status(201).json({ success: true, message: 'Farmer registered successfully', data: result.recordset[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateFarmer = async (req, res) => {
  try {
    const { name, village, district, phone, alternate_phone, email, bank_account, ifsc_code } = req.body;
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .input('name', sql.NVarChar, name)
      .input('village', sql.NVarChar, village)
      .input('district', sql.NVarChar, district)
      .input('phone', sql.NVarChar, phone)
      .input('alternate_phone', sql.NVarChar, alternate_phone || '')
      .input('email', sql.NVarChar, email || '')
      .input('bank_account', sql.NVarChar, bank_account || '')
      .input('ifsc_code', sql.NVarChar, ifsc_code || '')
      .query(`
        UPDATE Farmers SET name=@name, village=@village, district=@district,
          phone=@phone, alternate_phone=@alternate_phone, email=@email,
          bank_account=@bank_account, ifsc_code=@ifsc_code, updated_at=GETDATE()
        OUTPUT INSERTED.*
        WHERE id = @id
      `);
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Farmer not found' });
    }
    res.json({ success: true, message: 'Farmer updated successfully', data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteFarmer = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('DELETE FROM Farmers OUTPUT DELETED.id WHERE id = @id');
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Farmer not found' });
    }
    res.json({ success: true, message: 'Farmer deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllFarmers, getFarmerById, createFarmer, updateFarmer, deleteFarmer };
