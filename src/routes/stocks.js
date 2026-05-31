const express = require('express');
const router = express.Router();
const { getAllStocks, getStockById, createStock, updateStock, deleteStock, getStockSummary } = require('../controllers/stockController');
const authMiddleware = require('../middleware/auth');

router.use(authMiddleware);
router.get('/summary', getStockSummary);
router.get('/', getAllStocks);
router.get('/:id', getStockById);
router.post('/', createStock);
router.put('/:id', updateStock);
router.delete('/:id', deleteStock);

module.exports = router;
