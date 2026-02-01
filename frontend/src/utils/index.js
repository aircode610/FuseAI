/**
 * Utility Functions
 */

export const pluralize = (count, singular, plural = `${singular}s`) => {
  return count === 1 ? singular : plural;
};

export const formatMetric = (value, decimals = 2) => {
  if (value >= 1000000) return `${(value / 1000000).toFixed(decimals)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(decimals)}K`;
  return value.toString();
};

export const filterBySearchQuery = (items, query, fields = []) => {
  if (!query) return items;
  
  const lowerQuery = query.toLowerCase();
  return items.filter(item =>
    fields.some(field => 
      item[field]?.toLowerCase().includes(lowerQuery)
    )
  );
};

export const getThemeFromStorage = () => {
  return localStorage.getItem('fuseai-theme') || 'light';
};

export const setThemeInStorage = (theme) => {
  localStorage.setItem('fuseai-theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
};
