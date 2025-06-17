import React, { useState, useEffect } from 'react';
import './PaymentMethods.css';

interface PaymentMethod {
  id: string;
  type: 'crypto' | 'credit_card' | 'bank_transfer' | 'paypal';
  name: string;
  details: any;
  isDefault: boolean;
}

interface PaymentMethodsProps {
  userId: string;
  apiBaseUrl: string;
  onPaymentSelect?: (methodId: string) => void;
  jobAmount?: number;
  readOnly?: boolean;
}

const PaymentMethods: React.FC<PaymentMethodsProps> = ({
  userId,
  apiBaseUrl,
  onPaymentSelect,
  jobAmount,
  readOnly = false
}) => {
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedType, setSelectedType] = useState<PaymentMethod['type']>('crypto');
  const [formData, setFormData] = useState({
    name: '',
    details: {}
  });
  const [selectedMethodId, setSelectedMethodId] = useState<string | null>(null);

  // Fetch payment methods
  const fetchPaymentMethods = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBaseUrl}/payments/methods/${userId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch payment methods');
      }
      
      const data = await response.json();
      setPaymentMethods(data);
      
      // Select default payment method if available
      const defaultMethod = data.find((method: PaymentMethod) => method.isDefault);
      if (defaultMethod && onPaymentSelect) {
        setSelectedMethodId(defaultMethod.id);
        onPaymentSelect(defaultMethod.id);
      }
    } catch (err) {
      setError('Error loading payment methods. Please try again later.');
      console.error('Error fetching payment methods:', err);
    } finally {
      setLoading(false);
    }
  };

  // Add new payment method
  const addPaymentMethod = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/payments/methods/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: selectedType,
          name: formData.name,
          details: formData.details,
          isDefault: paymentMethods.length === 0 // Make default if it's the first one
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to add payment method');
      }
      
      // Refresh payment methods
      await fetchPaymentMethods();
      
      // Close modal and reset form
      setIsModalOpen(false);
      resetForm();
      
    } catch (err) {
      setError('Error adding payment method. Please try again.');
      console.error('Error adding payment method:', err);
    } finally {
      setLoading(false);
    }
  };

  // Set default payment method
  const setDefaultMethod = async (methodId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/payments/methods/${userId}/${methodId}/default`, {
        method: 'PUT'
      });
      
      if (!response.ok) {
        throw new Error('Failed to set default payment method');
      }
      
      // Update local state
      setPaymentMethods(paymentMethods.map(method => ({
        ...method,
        isDefault: method.id === methodId
      })));
      
    } catch (err) {
      setError('Error setting default payment method. Please try again.');
      console.error('Error setting default payment method:', err);
    } finally {
      setLoading(false);
    }
  };

  // Delete payment method
  const deletePaymentMethod = async (methodId: string) => {
    if (!window.confirm('Are you sure you want to delete this payment method?')) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/payments/methods/${userId}/${methodId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete payment method');
      }
      
      // Refresh payment methods
      await fetchPaymentMethods();
      
    } catch (err) {
      setError('Error deleting payment method. Please try again.');
      console.error('Error deleting payment method:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle payment method selection
  const handleSelectMethod = (methodId: string) => {
    setSelectedMethodId(methodId);
    if (onPaymentSelect) {
      onPaymentSelect(methodId);
    }
  };

  // Reset form data
  const resetForm = () => {
    setSelectedType('crypto');
    setFormData({
      name: '',
      details: {}
    });
  };

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Handle payment type specific field changes
  const handleDetailsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      details: {
        ...formData.details,
        [name]: value
      }
    });
  };

  // Load payment methods on component mount
  useEffect(() => {
    fetchPaymentMethods();
  }, [userId]);

  // Render payment method form based on selected type
  const renderPaymentForm = () => {
    switch (selectedType) {
      case 'crypto':
        return (
          <>
            <div className="form-group">
              <label htmlFor="walletAddress">Wallet Address</label>
              <input
                type="text"
                id="walletAddress"
                name="walletAddress"
                value={formData.details.walletAddress || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="network">Network</label>
              <input
                type="text"
                id="network"
                name="network"
                value={formData.details.network || ''}
                onChange={handleDetailsChange}
                required
                placeholder="e.g., Ethereum, Bitcoin, etc."
              />
            </div>
          </>
        );
        
      case 'credit_card':
        return (
          <>
            <div className="form-group">
              <label htmlFor="cardNumber">Card Number</label>
              <input
                type="text"
                id="cardNumber"
                name="cardNumber"
                value={formData.details.cardNumber || ''}
                onChange={handleDetailsChange}
                required
                placeholder="•••• •••• •••• ••••"
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="expiryDate">Expiry Date</label>
                <input
                  type="text"
                  id="expiryDate"
                  name="expiryDate"
                  value={formData.details.expiryDate || ''}
                  onChange={handleDetailsChange}
                  required
                  placeholder="MM/YY"
                />
              </div>
              <div className="form-group">
                <label htmlFor="cvv">CVV</label>
                <input
                  type="text"
                  id="cvv"
                  name="cvv"
                  value={formData.details.cvv || ''}
                  onChange={handleDetailsChange}
                  required
                  placeholder="123"
                />
              </div>
            </div>
            <div className="form-group">
              <label htmlFor="cardholderName">Cardholder Name</label>
              <input
                type="text"
                id="cardholderName"
                name="cardholderName"
                value={formData.details.cardholderName || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
          </>
        );
        
      case 'bank_transfer':
        return (
          <>
            <div className="form-group">
              <label htmlFor="accountName">Account Name</label>
              <input
                type="text"
                id="accountName"
                name="accountName"
                value={formData.details.accountName || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="accountNumber">Account Number</label>
              <input
                type="text"
                id="accountNumber"
                name="accountNumber"
                value={formData.details.accountNumber || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="bankName">Bank Name</label>
              <input
                type="text"
                id="bankName"
                name="bankName"
                value={formData.details.bankName || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="routingNumber">Routing Number</label>
              <input
                type="text"
                id="routingNumber"
                name="routingNumber"
                value={formData.details.routingNumber || ''}
                onChange={handleDetailsChange}
                required
              />
            </div>
          </>
        );
        
      case 'paypal':
        return (
          <div className="form-group">
            <label htmlFor="email">PayPal Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.details.email || ''}
              onChange={handleDetailsChange}
              required
            />
          </div>
        );
        
      default:
        return null;
    }
  };

  // Render payment method card based on type
  const renderPaymentMethodCard = (method: PaymentMethod) => {
    switch (method.type) {
      case 'crypto':
        return (
          <div className="payment-method-details">
            <div className="payment-method-icon crypto">₿</div>
            <div className="payment-method-info">
              <p className="payment-method-name">{method.name}</p>
              <p className="payment-method-detail">
                Wallet: {maskText(method.details.walletAddress)}
              </p>
              <p className="payment-method-detail">Network: {method.details.network}</p>
            </div>
          </div>
        );
        
      case 'credit_card':
        return (
          <div className="payment-method-details">
            <div className="payment-method-icon card">💳</div>
            <div className="payment-method-info">
              <p className="payment-method-name">{method.name}</p>
              <p className="payment-method-detail">
                Card: •••• {method.details.cardNumber.slice(-4)}
              </p>
              <p className="payment-method-detail">
                Expires: {method.details.expiryDate}
              </p>
            </div>
          </div>
        );
        
      case 'bank_transfer':
        return (
          <div className="payment-method-details">
            <div className="payment-method-icon bank">🏦</div>
            <div className="payment-method-info">
              <p className="payment-method-name">{method.name}</p>
              <p className="payment-method-detail">
                Account: •••• {method.details.accountNumber.slice(-4)}
              </p>
              <p className="payment-method-detail">Bank: {method.details.bankName}</p>
            </div>
          </div>
        );
        
      case 'paypal':
        return (
          <div className="payment-method-details">
            <div className="payment-method-icon paypal">P</div>
            <div className="payment-method-info">
              <p className="payment-method-name">{method.name}</p>
              <p className="payment-method-detail">
                Email: {maskEmail(method.details.email)}
              </p>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  // Helper function to mask sensitive text
  const maskText = (text: string) => {
    if (!text) return '';
    const firstChars = text.slice(0, 6);
    const lastChars = text.slice(-4);
    return `${firstChars}...${lastChars}`;
  };

  // Helper function to mask email
  const maskEmail = (email: string) => {
    if (!email) return '';
    const [username, domain] = email.split('@');
    const maskedUsername = username.charAt(0) + '•'.repeat(username.length - 2) + username.charAt(username.length - 1);
    return `${maskedUsername}@${domain}`;
  };

  return (
    <div className="payment-methods">
      <div className="payment-methods-header">
        <h2>Payment Methods</h2>
        {!readOnly && (
          <button 
            className="add-payment-btn"
            onClick={() => setIsModalOpen(true)}
          >
            Add Payment Method
          </button>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading && !paymentMethods.length ? (
        <div className="loading-indicator">Loading payment methods...</div>
      ) : paymentMethods.length === 0 ? (
        <div className="empty-payment-methods">
          <p>No payment methods added yet.</p>
          {!readOnly && (
            <p>Add a payment method to receive payments for your work.</p>
          )}
        </div>
      ) : (
        <div className="payment-methods-list">
          {paymentMethods.map(method => (
            <div 
              key={method.id} 
              className={`payment-method-card ${method.isDefault ? 'default' : ''} ${selectedMethodId === method.id ? 'selected' : ''}`}
              onClick={() => !readOnly && handleSelectMethod(method.id)}
            >
              {renderPaymentMethodCard(method)}
              
              {!readOnly && (
                <div className="payment-method-actions">
                  {!method.isDefault && (
                    <button 
                      className="set-default-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDefaultMethod(method.id);
                      }}
                    >
                      Set as Default
                    </button>
                  )}
                  <button 
                    className="delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      deletePaymentMethod(method.id);
                    }}
                  >
                    Delete
                  </button>
                </div>
              )}
              
              {method.isDefault && (
                <div className="default-badge">Default</div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {jobAmount && selectedMethodId && (
        <div className="payment-summary">
          <h3>Payment Summary</h3>
          <div className="payment-amount">
            <span>Amount:</span>
            <span>${jobAmount.toFixed(2)}</span>
          </div>
          <div className="payment-fee">
            <span>Processing Fee:</span>
            <span>${(jobAmount * 0.025).toFixed(2)}</span>
          </div>
          <div className="payment-total">
            <span>Total:</span>
            <span>${(jobAmount * 1.025).toFixed(2)}</span>
          </div>
        </div>
      )}
      
      {isModalOpen && !readOnly && (
        <div className="modal-overlay">
          <div className="payment-modal">
            <h3>Add Payment Method</h3>
            
            <div className="payment-type-selector">
              <button 
                className={`type-btn ${selectedType === 'crypto' ? 'active' : ''}`}
                onClick={() => setSelectedType('crypto')}
              >
                Crypto
              </button>
              <button 
                className={`type-btn ${selectedType === 'credit_card' ? 'active' : ''}`}
                onClick={() => setSelectedType('credit_card')}
              >
                Credit Card
              </button>
              <button 
                className={`type-btn ${selectedType === 'bank_transfer' ? 'active' : ''}`}
                onClick={() => setSelectedType('bank_transfer')}
              >
                Bank Transfer
              </button>
              <button 
                className={`type-btn ${selectedType === 'paypal' ? 'active' : ''}`}
                onClick={() => setSelectedType('paypal')}
              >
                PayPal
              </button>
            </div>
            
            <form onSubmit={addPaymentMethod}>
              <div className="form-group">
                <label htmlFor="name">Payment Method Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  placeholder="e.g., My Ethereum Wallet"
                />
              </div>
              
              {renderPaymentForm()}
              
              <div className="modal-actions">
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => {
                    setIsModalOpen(false);
                    resetForm();
                  }}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="save-btn"
                  disabled={loading}
                >
                  {loading ? 'Adding...' : 'Add Payment Method'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentMethods;
