export const CATEGORY_COLORS = {
  VCB: '#2196F3',
  ACB_HGS: '#4CAF50',
  ACB_LARGE: '#009688',
  MCCB: '#FF9800',
  MC: '#9C27B0',
  RELAY: '#F44336',
  SPARE: '#795548',
  UNKNOWN: '#9E9E9E',
}

export function getCategoryColor(category) {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.UNKNOWN
}
