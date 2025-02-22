document.addEventListener('DOMContentLoaded', () => {
    const addProductBtn = document.getElementById('addProductBtn');
    const addProductModal = document.getElementById('addProductModal');
    const addProductForm = document.getElementById('addProductForm');
    const cancelAddBtn = document.getElementById('cancelAdd');
    const inventoryList = document.getElementById('inventoryList');
    const reminderList = document.getElementById('reminderList');

    // API endpoints
    const API_BASE_URL = 'http://localhost:5000/api';

    // Show modal
    addProductBtn.addEventListener('click', () => {
        addProductModal.style.display = 'block';
    });

    // Hide modal
    cancelAddBtn.addEventListener('click', () => {
        addProductModal.style.display = 'none';
        addProductForm.reset();
    });

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === addProductModal) {
            addProductModal.style.display = 'none';
            addProductForm.reset();
        }
    });

    // Handle form submission
    addProductForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const productData = {
            name: document.getElementById('productName').value,
            quantity: parseInt(document.getElementById('quantity').value),
            expiration_date: document.getElementById('expirationDate').value,
            reminder_frequency: parseInt(document.getElementById('reminderFrequency').value),
            minimum_stock: parseInt(document.getElementById('minimumStock').value)
        };

        try {
            const response = await fetch(`${API_BASE_URL}/products`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(productData)
            });

            if (response.ok) {
                addProductModal.style.display = 'none';
                addProductForm.reset();
                loadInventory();
                loadReminders();
                updateDashboard();
            } else {
                throw new Error('Failed to add product');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to add product');
        }
    });

    // Load inventory
    async function loadInventory() {
        try {
            const response = await fetch(`${API_BASE_URL}/products`);
            const products = await response.json();
            
            inventoryList.innerHTML = products.map(product => `
                <div class="product-card">
                    <h3>${product.name}</h3>
                    <p>Quantity: ${product.quantity}</p>
                    <p>Expiration: ${new Date(product.expiration_date).toLocaleDateString()}</p>
                    <p>Minimum Stock: ${product.minimum_stock}</p>
                    <div class="product-actions">
                        <button onclick="updateQuantity(${product.id}, -1)" class="btn-secondary">-</button>
                        <button onclick="updateQuantity(${product.id}, 1)" class="btn-secondary">+</button>
                        <button onclick="deleteProduct(${product.id})" class="btn-primary">Delete</button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to load inventory');
        }
    }

    // Load reminders
    async function loadReminders() {
        try {
            const response = await fetch(`${API_BASE_URL}/reminders`);
            const reminders = await response.json();
            
            reminderList.innerHTML = reminders.map(reminder => `
                <div class="reminder-card">
                    <h3>${reminder.product_name}</h3>
                    <p>${reminder.message}</p>
                    <p>Due: ${new Date(reminder.due_date).toLocaleDateString()}</p>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to load reminders');
        }
    }

    // Update dashboard
    async function updateDashboard() {
        try {
            const response = await fetch(`${API_BASE_URL}/dashboard`);
            const stats = await response.json();
            
            document.getElementById('totalProducts').textContent = stats.total_products;
            document.getElementById('lowStock').textContent = stats.low_stock;
            document.getElementById('expiringSoon').textContent = stats.expiring_soon;
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to update dashboard');
        }
    }

    // Update product quantity
    window.updateQuantity = async (productId, change) => {
        try {
            const response = await fetch(`${API_BASE_URL}/products/${productId}/quantity`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ change })
            });

            if (response.ok) {
                loadInventory();
                updateDashboard();
            } else {
                throw new Error('Failed to update quantity');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to update quantity');
        }
    };

    // Delete product
    window.deleteProduct = async (productId) => {
        if (confirm('Are you sure you want to delete this product?')) {
            try {
                const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    loadInventory();
                    loadReminders();
                    updateDashboard();
                } else {
                    throw new Error('Failed to delete product');
                }
            } catch (error) {
                console.error('Error:', error);
                showAlert('Failed to delete product');
            }
        }
    };

    // Show alert
    function showAlert(message) {
        const alertsContainer = document.getElementById('alertsContainer');
        const alert = document.createElement('div');
        alert.className = 'alert';
        alert.textContent = message;
        alertsContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    // Initial load
    loadInventory();
    loadReminders();
    updateDashboard();
});
function sendEmailAlert() {
    fetch("http://127.0.0.1:5000/send_alert", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email: "user@example.com",  // Replace with actual recipient email
            subject: "Stock Low Alert",
            message: "Your inventory is running low. Please restock soon!",
        }),
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error("Error:", error));
}

function testApiCall() {
    fetch("http://127.0.0.1:5000/some-endpoint") // Change "/some-endpoint" to your actual API route
    .then(response => response.json())
    .then(data => console.log("API Response:", data)) // Logs data in Console
    .catch(error => console.error("Error:", error));
}

// Call function when page loads
window.onload = testApiCall;
