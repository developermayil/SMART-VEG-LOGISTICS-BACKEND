const express = require('express');
const router = express.Router();
const { getAllFarmers, getFarmerById, createFarmer, updateFarmer, deleteFarmer } = require('../controllers/farmerController');
const authMiddleware = require('../middleware/auth');

router.use(authMiddleware);
router.get('/', getAllFarmers);
router.get('/:id', getFarmerById);
router.post('/', createFarmer);
router.put('/:id', updateFarmer);
router.delete('/:id', deleteFarmer);

module.exports = router;
