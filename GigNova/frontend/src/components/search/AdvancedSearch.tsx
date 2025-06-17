import React, { useState, useEffect } from 'react';
import './AdvancedSearch.css';

interface SearchFilters {
  query: string;
  category: string;
  skills: string[];
  priceMin: number;
  priceMax: number;
  datePosted: string;
  location: string;
  sortBy: string;
  page: number;
  limit: number;
}

interface SearchResult {
  id: string;
  title: string;
  description: string;
  skills: string[];
  budget_min: number;
  budget_max: number;
  deadline: string;
  status: string;
  client_id: string;
  client_name: string;
  created_at: string;
  location?: string;
}

interface AdvancedSearchProps {
  apiBaseUrl: string;
  onResultSelect?: (result: SearchResult) => void;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({ apiBaseUrl, onResultSelect }) => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    category: '',
    skills: [],
    priceMin: 0,
    priceMax: 10000,
    datePosted: '',
    location: '',
    sortBy: 'relevance',
    page: 1,
    limit: 10
  });
  
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [categories, setCategories] = useState<string[]>([]);
  const [popularSkills, setPopularSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Fetch categories and popular skills
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [categoriesRes, skillsRes] = await Promise.all([
          fetch(`${apiBaseUrl}/metadata/categories`),
          fetch(`${apiBaseUrl}/metadata/skills/popular`)
        ]);
        
        if (categoriesRes.ok && skillsRes.ok) {
          const categoriesData = await categoriesRes.json();
          const skillsData = await skillsRes.json();
          
          setCategories(categoriesData);
          setPopularSkills(skillsData);
        }
      } catch (err) {
        console.error('Error fetching metadata:', err);
      }
    };
    
    fetchMetadata();
  }, [apiBaseUrl]);
  
  // Search function
  const performSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build query parameters
      const queryParams = new URLSearchParams();
      if (filters.query) queryParams.append('query', filters.query);
      if (filters.category) queryParams.append('category', filters.category);
      if (filters.skills.length) queryParams.append('skills', filters.skills.join(','));
      queryParams.append('price_min', filters.priceMin.toString());
      queryParams.append('price_max', filters.priceMax.toString());
      if (filters.datePosted) queryParams.append('date_posted', filters.datePosted);
      if (filters.location) queryParams.append('location', filters.location);
      queryParams.append('sort_by', filters.sortBy);
      queryParams.append('page', filters.page.toString());
      queryParams.append('limit', filters.limit.toString());
      
      const response = await fetch(`${apiBaseUrl}/jobs/search?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error('Search failed');
      }
      
      const data = await response.json();
      setResults(data.results);
      setTotalResults(data.total);
    } catch (err) {
      setError('Error performing search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle search form submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch();
  };
  
  // Handle filter changes
  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'number') {
      setFilters({
        ...filters,
        [name]: parseFloat(value)
      });
    } else {
      setFilters({
        ...filters,
        [name]: value
      });
    }
  };
  
  // Add skill to filters
  const addSkill = () => {
    if (skillInput && !filters.skills.includes(skillInput)) {
      setFilters({
        ...filters,
        skills: [...filters.skills, skillInput]
      });
      setSkillInput('');
    }
  };
  
  // Remove skill from filters
  const removeSkill = (skill: string) => {
    setFilters({
      ...filters,
      skills: filters.skills.filter(s => s !== skill)
    });
  };
  
  // Add popular skill to filters
  const addPopularSkill = (skill: string) => {
    if (!filters.skills.includes(skill)) {
      setFilters({
        ...filters,
        skills: [...filters.skills, skill]
      });
    }
  };
  
  // Handle pagination
  const handlePageChange = (newPage: number) => {
    setFilters({
      ...filters,
      page: newPage
    });
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Perform search with new page
    performSearch();
  };
  
  // Clear all filters
  const clearFilters = () => {
    setFilters({
      query: '',
      category: '',
      skills: [],
      priceMin: 0,
      priceMax: 10000,
      datePosted: '',
      location: '',
      sortBy: 'relevance',
      page: 1,
      limit: 10
    });
  };
  
  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };
  
  // Calculate days remaining until deadline
  const calculateDaysRemaining = (deadlineString: string) => {
    const deadline = new Date(deadlineString);
    const today = new Date();
    const diffTime = deadline.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };
  
  return (
    <div className="advanced-search">
      <div className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-bar">
            <input
              type="text"
              name="query"
              value={filters.query}
              onChange={handleFilterChange}
              placeholder="Search for jobs..."
              className="search-input"
            />
            <button type="submit" className="search-button">
              Search
            </button>
            <button 
              type="button" 
              className="filter-toggle-button"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>
          
          {showFilters && (
            <div className="advanced-filters">
              <div className="filter-section">
                <h3>Categories</h3>
                <select
                  name="category"
                  value={filters.category}
                  onChange={handleFilterChange}
                  className="filter-select"
                >
                  <option value="">All Categories</option>
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="filter-section">
                <h3>Skills</h3>
                <div className="skills-input">
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    placeholder="Add a skill..."
                    className="skill-input"
                  />
                  <button 
                    type="button" 
                    onClick={addSkill}
                    className="add-skill-button"
                  >
                    Add
                  </button>
                </div>
                
                {filters.skills.length > 0 && (
                  <div className="selected-skills">
                    {filters.skills.map(skill => (
                      <span key={skill} className="skill-tag">
                        {skill}
                        <button 
                          type="button" 
                          onClick={() => removeSkill(skill)}
                          className="remove-skill"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                
                <div className="popular-skills">
                  <h4>Popular Skills:</h4>
                  <div className="popular-skills-list">
                    {popularSkills.map(skill => (
                      <button
                        key={skill}
                        type="button"
                        onClick={() => addPopularSkill(skill)}
                        className={`popular-skill ${filters.skills.includes(skill) ? 'selected' : ''}`}
                        disabled={filters.skills.includes(skill)}
                      >
                        {skill}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="filter-section">
                <h3>Budget Range</h3>
                <div className="price-range">
                  <div className="price-input">
                    <label htmlFor="priceMin">Min ($)</label>
                    <input
                      type="number"
                      id="priceMin"
                      name="priceMin"
                      value={filters.priceMin}
                      onChange={handleFilterChange}
                      min="0"
                      className="price-field"
                    />
                  </div>
                  <div className="price-input">
                    <label htmlFor="priceMax">Max ($)</label>
                    <input
                      type="number"
                      id="priceMax"
                      name="priceMax"
                      value={filters.priceMax}
                      onChange={handleFilterChange}
                      min="0"
                      className="price-field"
                    />
                  </div>
                </div>
              </div>
              
              <div className="filter-section">
                <h3>Date Posted</h3>
                <select
                  name="datePosted"
                  value={filters.datePosted}
                  onChange={handleFilterChange}
                  className="filter-select"
                >
                  <option value="">Any Time</option>
                  <option value="today">Today</option>
                  <option value="week">Past Week</option>
                  <option value="month">Past Month</option>
                  <option value="3months">Past 3 Months</option>
                </select>
              </div>
              
              <div className="filter-section">
                <h3>Location</h3>
                <input
                  type="text"
                  name="location"
                  value={filters.location}
                  onChange={handleFilterChange}
                  placeholder="Any Location"
                  className="filter-input"
                />
              </div>
              
              <div className="filter-section">
                <h3>Sort By</h3>
                <select
                  name="sortBy"
                  value={filters.sortBy}
                  onChange={handleFilterChange}
                  className="filter-select"
                >
                  <option value="relevance">Relevance</option>
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="budget_high">Highest Budget</option>
                  <option value="budget_low">Lowest Budget</option>
                  <option value="deadline">Deadline (Soonest)</option>
                </select>
              </div>
              
              <div className="filter-actions">
                <button 
                  type="button" 
                  onClick={clearFilters}
                  className="clear-filters-button"
                >
                  Clear All Filters
                </button>
                <button type="submit" className="apply-filters-button">
                  Apply Filters
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
      
      <div className="search-results-container">
        {error && <div className="search-error">{error}</div>}
        
        {loading ? (
          <div className="loading-results">Searching for jobs...</div>
        ) : results.length === 0 ? (
          <div className="no-results">
            <h3>No jobs found</h3>
            <p>Try adjusting your search filters or try a different search term.</p>
          </div>
        ) : (
          <>
            <div className="results-header">
              <h2>Search Results</h2>
              <span className="results-count">{totalResults} jobs found</span>
            </div>
            
            <div className="search-results">
              {results.map(result => (
                <div 
                  key={result.id} 
                  className="search-result-card"
                  onClick={() => onResultSelect && onResultSelect(result)}
                >
                  <div className="result-header">
                    <h3 className="result-title">{result.title}</h3>
                    <div className="result-budget">
                      ${result.budget_min} - ${result.budget_max}
                    </div>
                  </div>
                  
                  <p className="result-description">
                    {result.description.length > 150
                      ? `${result.description.substring(0, 150)}...`
                      : result.description}
                  </p>
                  
                  <div className="result-skills">
                    {result.skills.slice(0, 5).map(skill => (
                      <span key={skill} className="result-skill-tag">
                        {skill}
                      </span>
                    ))}
                    {result.skills.length > 5 && (
                      <span className="more-skills">+{result.skills.length - 5} more</span>
                    )}
                  </div>
                  
                  <div className="result-meta">
                    <div className="result-client">
                      <span className="meta-label">Client:</span>
                      <span>{result.client_name}</span>
                    </div>
                    
                    {result.location && (
                      <div className="result-location">
                        <span className="meta-label">Location:</span>
                        <span>{result.location}</span>
                      </div>
                    )}
                    
                    <div className="result-dates">
                      <div className="posted-date">
                        <span className="meta-label">Posted:</span>
                        <span>{formatDate(result.created_at)}</span>
                      </div>
                      
                      <div className="deadline-date">
                        <span className="meta-label">Deadline:</span>
                        <span>
                          {formatDate(result.deadline)}
                          <span className="days-remaining">
                            ({calculateDaysRemaining(result.deadline)} days left)
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {totalResults > filters.limit && (
              <div className="pagination">
                <button
                  className="pagination-button"
                  disabled={filters.page === 1}
                  onClick={() => handlePageChange(filters.page - 1)}
                >
                  Previous
                </button>
                
                <div className="page-numbers">
                  {Array.from({ length: Math.ceil(totalResults / filters.limit) }, (_, i) => i + 1)
                    .filter(page => {
                      const currentPage = filters.page;
                      return page === 1 || 
                             page === Math.ceil(totalResults / filters.limit) || 
                             Math.abs(page - currentPage) < 3;
                    })
                    .map((page, index, array) => {
                      // Add ellipsis
                      if (index > 0 && page - array[index - 1] > 1) {
                        return (
                          <React.Fragment key={`ellipsis-${page}`}>
                            <span className="ellipsis">...</span>
                            <button
                              className={`page-number ${filters.page === page ? 'active' : ''}`}
                              onClick={() => handlePageChange(page)}
                            >
                              {page}
                            </button>
                          </React.Fragment>
                        );
                      }
                      
                      return (
                        <button
                          key={page}
                          className={`page-number ${filters.page === page ? 'active' : ''}`}
                          onClick={() => handlePageChange(page)}
                        >
                          {page}
                        </button>
                      );
                    })}
                </div>
                
                <button
                  className="pagination-button"
                  disabled={filters.page === Math.ceil(totalResults / filters.limit)}
                  onClick={() => handlePageChange(filters.page + 1)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdvancedSearch;
