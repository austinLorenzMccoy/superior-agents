import React, { useState, useEffect } from 'react';
import './PortfolioShowcase.css';

interface PortfolioItem {
  id: string;
  title: string;
  description: string;
  imageUrl: string;
  tags: string[];
  projectUrl?: string;
  completionDate: string;
}

interface PortfolioShowcaseProps {
  userId: string;
  isEditable?: boolean;
  apiBaseUrl: string;
}

const PortfolioShowcase: React.FC<PortfolioShowcaseProps> = ({ 
  userId, 
  isEditable = false,
  apiBaseUrl 
}) => {
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<PortfolioItem | null>(null);
  const [formData, setFormData] = useState<Partial<PortfolioItem>>({
    title: '',
    description: '',
    imageUrl: '',
    tags: [],
    projectUrl: '',
    completionDate: new Date().toISOString().split('T')[0]
  });

  // Fetch portfolio items
  const fetchPortfolioItems = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBaseUrl}/portfolio/${userId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch portfolio items');
      }
      
      const data = await response.json();
      setPortfolioItems(data);
    } catch (err) {
      setError('Error loading portfolio items. Please try again later.');
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Handle tags input
  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tags = e.target.value.split(',').map(tag => tag.trim());
    setFormData({
      ...formData,
      tags
    });
  };

  // Save portfolio item
  const savePortfolioItem = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      const method = currentItem ? 'PUT' : 'POST';
      const url = currentItem 
        ? `${apiBaseUrl}/portfolio/${userId}/${currentItem.id}` 
        : `${apiBaseUrl}/portfolio/${userId}`;
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save portfolio item');
      }
      
      // Refresh portfolio items
      await fetchPortfolioItems();
      
      // Close modal and reset form
      setIsModalOpen(false);
      setCurrentItem(null);
      setFormData({
        title: '',
        description: '',
        imageUrl: '',
        tags: [],
        projectUrl: '',
        completionDate: new Date().toISOString().split('T')[0]
      });
      
    } catch (err) {
      setError('Error saving portfolio item. Please try again.');
      console.error('Error saving portfolio item:', err);
    } finally {
      setLoading(false);
    }
  };

  // Delete portfolio item
  const deletePortfolioItem = async (itemId: string) => {
    if (!window.confirm('Are you sure you want to delete this portfolio item?')) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${apiBaseUrl}/portfolio/${userId}/${itemId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete portfolio item');
      }
      
      // Refresh portfolio items
      await fetchPortfolioItems();
      
    } catch (err) {
      setError('Error deleting portfolio item. Please try again.');
      console.error('Error deleting portfolio item:', err);
    } finally {
      setLoading(false);
    }
  };

  // Edit portfolio item
  const editPortfolioItem = (item: PortfolioItem) => {
    setCurrentItem(item);
    setFormData({
      title: item.title,
      description: item.description,
      imageUrl: item.imageUrl,
      tags: item.tags,
      projectUrl: item.projectUrl || '',
      completionDate: item.completionDate
    });
    setIsModalOpen(true);
  };

  // Load portfolio items on component mount
  useEffect(() => {
    fetchPortfolioItems();
  }, [userId]);

  return (
    <div className="portfolio-showcase">
      <div className="portfolio-header">
        <h2>Portfolio</h2>
        {isEditable && (
          <button 
            className="add-portfolio-btn"
            onClick={() => {
              setCurrentItem(null);
              setFormData({
                title: '',
                description: '',
                imageUrl: '',
                tags: [],
                projectUrl: '',
                completionDate: new Date().toISOString().split('T')[0]
              });
              setIsModalOpen(true);
            }}
          >
            Add Project
          </button>
        )}
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      {loading && !portfolioItems.length ? (
        <div className="loading-indicator">Loading portfolio...</div>
      ) : portfolioItems.length === 0 ? (
        <div className="empty-portfolio">
          <p>No portfolio items yet.</p>
          {isEditable && (
            <p>Showcase your best work by adding projects to your portfolio.</p>
          )}
        </div>
      ) : (
        <div className="portfolio-grid">
          {portfolioItems.map(item => (
            <div key={item.id} className="portfolio-item">
              <div className="portfolio-image">
                <img src={item.imageUrl} alt={item.title} />
                {isEditable && (
                  <div className="portfolio-actions">
                    <button 
                      className="edit-btn"
                      onClick={() => editPortfolioItem(item)}
                    >
                      Edit
                    </button>
                    <button 
                      className="delete-btn"
                      onClick={() => deletePortfolioItem(item.id)}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
              <div className="portfolio-details">
                <h3>{item.title}</h3>
                <p className="portfolio-date">Completed: {new Date(item.completionDate).toLocaleDateString()}</p>
                <p className="portfolio-description">{item.description}</p>
                <div className="portfolio-tags">
                  {item.tags.map((tag, index) => (
                    <span key={index} className="tag">{tag}</span>
                  ))}
                </div>
                {item.projectUrl && (
                  <a 
                    href={item.projectUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="project-link"
                  >
                    View Project
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="portfolio-modal">
            <h3>{currentItem ? 'Edit Project' : 'Add New Project'}</h3>
            
            <form onSubmit={savePortfolioItem}>
              <div className="form-group">
                <label htmlFor="title">Project Title</label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                  rows={4}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="imageUrl">Image URL</label>
                <input
                  type="url"
                  id="imageUrl"
                  name="imageUrl"
                  value={formData.imageUrl}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="tags">Tags (comma-separated)</label>
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  value={formData.tags?.join(', ')}
                  onChange={handleTagsChange}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="projectUrl">Project URL (optional)</label>
                <input
                  type="url"
                  id="projectUrl"
                  name="projectUrl"
                  value={formData.projectUrl}
                  onChange={handleInputChange}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="completionDate">Completion Date</label>
                <input
                  type="date"
                  id="completionDate"
                  name="completionDate"
                  value={formData.completionDate}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="modal-actions">
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="save-btn"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioShowcase;
