const express = require('express');
const router = express.Router();
const { getAllDeliveries, getDeliveryById, createDelivery, updateDeliveryStatus, deleteDelivery } = require('../controllers/deliveryController');
const authMiddleware = require('../middleware/auth');

router.use(authMiddleware);
router.get('/', getAllDeliveries);
router.get('/:id', getDeliveryById);
router.post('/', createDelivery);
router.patch('/:id/status', updateDeliveryStatus);
router.delete('/:id', deleteDelivery);

module.exports = router;
