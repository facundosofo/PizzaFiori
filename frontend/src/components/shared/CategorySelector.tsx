/**
 * CategorySelector - Componente reutilizable para seleccionar categorías
 * Usado en tablas y análisis con dropdown personalizado
 */

import { useState, useRef, useEffect } from 'react';
import '../../styles/shared/category-selector.css';

interface CategorySelectorProps {
  categories: string[];
  selectedCategory?: string;
  onCategoryChange: (category: string) => void;
}

const CategorySelector = ({ 
  categories, 
  selectedCategory, 
  onCategoryChange 
}: CategorySelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const allOptions = [
    { value: '', label: 'Todas las categorías' },
    ...categories.map(cat => ({ value: cat, label: cat })),
  ];

  const selectedOption = allOptions.find(opt => opt.value === (selectedCategory || ''));

  return (
    <div className="category-selector" ref={dropdownRef}>
      <button
        className="category-selector-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        {selectedOption?.label || 'Categoría'}
        <span className={`chevron ${isOpen ? 'open' : ''}`}>▼</span>
      </button>

      {isOpen && (
        <div className="category-dropdown">
          {allOptions.map((option) => (
            <button
              key={option.value}
              className={`category-option ${selectedCategory === option.value ? 'active' : ''}`}
              onClick={() => {
                onCategoryChange(option.value);
                setIsOpen(false);
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default CategorySelector;
