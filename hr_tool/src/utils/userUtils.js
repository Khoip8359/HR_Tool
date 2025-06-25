// User utility functions
export const formatUserId = (samAccount) => {
  if (!samAccount || typeof samAccount !== 'string') {
    return ''
  }
  
  // Remove 'u' prefix if exists and add '0' prefix
  const cleanId = samAccount.startsWith('u') ? samAccount.substring(1) : samAccount
  return cleanId.length > 0 ? `0${cleanId}` : cleanId
}

export const extractUserId = (samAccount) => {
  if (!samAccount || typeof samAccount !== 'string') {
    return ''
  }
  
  // Remove 'u' prefix if exists
  return samAccount.startsWith('u') ? samAccount.substring(1) : samAccount
}

export const validateUserId = (userId) => {
  if (!userId || typeof userId !== 'string') {
    return false
  }
  
  // Basic validation - should be alphanumeric and not empty
  return /^[a-zA-Z0-9]+$/.test(userId.trim())
}

export const formatDisplayName = (displayName) => {
  if (!displayName || typeof displayName !== 'string') {
    return 'Unknown User'
  }
  
  return displayName.trim()
}

export const formatDepartment = (department) => {
  if (!department || typeof department !== 'string') {
    return 'N/A'
  }
  
  return department.trim()
}

// Date formatting utilities
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'N/A'
    
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch {
    return 'N/A'
  }
}

export const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) return 'N/A'
    
    return date.toLocaleString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'N/A'
  }
}

// Leave duration formatting
export const formatLeaveDuration = (quantity) => {
  if (!quantity) return '0'
  
  const num = parseFloat(quantity)
  if (isNaN(num)) return '0'
  
  if (num === 0.0625) return '30 phút (nửa giờ)'
  if (num === 0.5) return '0.5 ngày (4 giờ)'
  if (num === 1) return '1 ngày (8 giờ)'
  
  return num < 1 ? `${(num * 8).toFixed(1)} giờ` : `${num.toFixed(1)} ngày`
}

// Permission utilities
export const hasPermission = (userPermissions, requiredPermission) => {
  if (!userPermissions || !Array.isArray(userPermissions)) {
    return false
  }
  
  return userPermissions.includes(requiredPermission)
}

export const isManager = (userInfo) => {
  return userInfo?.isManager === true
}

// Storage utilities
export const getStorageType = (rememberMe) => {
  return rememberMe ? 'localStorage' : 'sessionStorage'
}

export const getStorageKey = (key) => {
  return `hr_tool_${key}`
} 