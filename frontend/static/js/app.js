// API Configuration

// Currency formatting helper
function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    if (typeof amount !== 'number' || isNaN(amount)) return '';
    return amount.toLocaleString(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
const API_URL = `${window.location.protocol}//${window.location.host}/api`;
console.log('API_URL:', API_URL);

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Simple YAML Parser for categorization rules import
function parseYAML(yamlText) {
    const result = {};
    let currentKey = null;
    let currentArray = null;
    let currentObject = null;
    let inArray = false;
    
    const lines = yamlText.split('\n');
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Skip empty lines and comments
        if (!trimmed || trimmed.startsWith('#')) continue;
        
        // Calculate indentation
        const indent = line.search(/\S/);
        
        // Check for array item
        if (trimmed.startsWith('- ')) {
            const content = trimmed.substring(2).trim();
            
            // Start of new object in array
            if (content.includes(':')) {
                if (currentKey && !result[currentKey]) {
                    result[currentKey] = [];
                }
                currentObject = {};
                currentArray = result[currentKey];
                
                // Parse inline key-value
                const colonIndex = content.indexOf(':');
                const key = content.substring(0, colonIndex).trim();
                let value = content.substring(colonIndex + 1).trim();
                value = parseYAMLValue(value);
                currentObject[key] = value;
            } else {
                // Simple array item
                if (currentArray) {
                    currentArray.push(parseYAMLValue(content));
                }
            }
        } else if (trimmed.includes(':')) {
            const colonIndex = trimmed.indexOf(':');
            const key = trimmed.substring(0, colonIndex).trim();
            let value = trimmed.substring(colonIndex + 1).trim();
            
            if (value === '' || value === '|' || value === '>') {
                // This is a key for a nested object or array
                if (indent === 0) {
                    currentKey = key;
                    result[currentKey] = [];
                    currentArray = result[currentKey];
                    inArray = true;
                }
            } else {
                // Key-value pair
                value = parseYAMLValue(value);
                
                if (currentObject && indent > 0) {
                    currentObject[key] = value;
                } else {
                    result[key] = value;
                }
            }
        }
        
        // Check if we need to push current object to array
        if (currentObject && currentArray) {
            const nextLine = lines[i + 1];
            if (!nextLine || nextLine.trim().startsWith('- ') || nextLine.trim() === '' || nextLine.search(/\S/) === 0) {
                if (Object.keys(currentObject).length > 0) {
                    currentArray.push(currentObject);
                    currentObject = null;
                }
            }
        }
    }
    
    // Push final object if exists
    if (currentObject && currentArray && Object.keys(currentObject).length > 0) {
        currentArray.push(currentObject);
    }
    
    return result;
}

function parseYAMLValue(value) {
    if (!value) return '';
    
    // Remove quotes
    if ((value.startsWith('"') && value.endsWith('"')) || 
        (value.startsWith("'") && value.endsWith("'"))) {
        return value.slice(1, -1);
    }
    
    // Parse booleans
    if (value.toLowerCase() === 'true') return true;
    if (value.toLowerCase() === 'false') return false;
    
    // Parse numbers
    if (!isNaN(value) && value !== '') {
        return Number(value);
    }
    
    return value;
}

// Convert object to YAML string
function toYAML(obj, indent = 0) {
    let result = '';
    const prefix = '  '.repeat(indent);
    
    if (Array.isArray(obj)) {
        obj.forEach(item => {
            if (typeof item === 'object' && item !== null) {
                const keys = Object.keys(item);
                keys.forEach((key, index) => {
                    const value = item[key];
                    if (index === 0) {
                        result += `${prefix}- ${key}: ${formatYAMLValue(value)}\n`;
                    } else {
                        result += `${prefix}  ${key}: ${formatYAMLValue(value)}\n`;
                    }
                });
                result += '\n';
            } else {
                result += `${prefix}- ${formatYAMLValue(item)}\n`;
            }
        });
    } else if (typeof obj === 'object' && obj !== null) {
        Object.keys(obj).forEach(key => {
            const value = obj[key];
            if (Array.isArray(value)) {
                result += `${prefix}${key}:\n`;
                result += toYAML(value, indent + 1);
            } else if (typeof value === 'object' && value !== null) {
                result += `${prefix}${key}:\n`;
                result += toYAML(value, indent + 1);
            } else {
                result += `${prefix}${key}: ${formatYAMLValue(value)}\n`;
            }
        });
    }
    
    return result;
}

function formatYAMLValue(value) {
    if (typeof value === 'string') {
        // Quote strings that contain special characters
        if (value.includes(',') || value.includes(':') || value.includes('#') || 
            value.includes('\n') || value.startsWith(' ') || value.endsWith(' ')) {
            return `"${value.replace(/"/g, '\\"')}"`;
        }
        return value;
    }
    return String(value);
}

// Badí' (Bahá'í) Calendar Configuration
const BADI_MONTHS = [
    { number: 1, name: "Bahá", arabic: "بهاء", meaning: "Splendour" },
    { number: 2, name: "Jalál", arabic: "جلال", meaning: "Glory" },
    { number: 3, name: "Jamál", arabic: "جمال", meaning: "Beauty" },
    { number: 4, name: "'Aẓamat", arabic: "عظمة", meaning: "Grandeur" },
    { number: 5, name: "Núr", arabic: "نور", meaning: "Light" },
    { number: 6, name: "Raḥmat", arabic: "رحمة", meaning: "Mercy" },
    { number: 7, name: "Kalimát", arabic: "كلمات", meaning: "Words" },
    { number: 8, name: "Kamál", arabic: "كمال", meaning: "Perfection" },
    { number: 9, name: "Asmá'", arabic: "أسماء", meaning: "Names" },
    { number: 10, name: "'Izzat", arabic: "عزة", meaning: "Might" },
    { number: 11, name: "Mashíyyat", arabic: "مشية", meaning: "Will" },
    { number: 12, name: "'Ilm", arabic: "علم", meaning: "Knowledge" },
    { number: 13, name: "Qudrat", arabic: "قدرة", meaning: "Power" },
    { number: 14, name: "Qawl", arabic: "قول", meaning: "Speech" },
    { number: 15, name: "Masá'il", arabic: "مسائل", meaning: "Questions" },
    { number: 16, name: "Sharaf", arabic: "شرف", meaning: "Honour" },
    { number: 17, name: "Sulṭán", arabic: "سلطان", meaning: "Sovereignty" },
    { number: 18, name: "Mulk", arabic: "ملك", meaning: "Dominion" },
    { number: 0, name: "Ayyám-i-Há", arabic: "أيام الهاء", meaning: "Intercalary Days" },
    { number: 19, name: "'Alá'", arabic: "علاء", meaning: "Loftiness" }
];

// Badí' Calendar Helper Functions
function getNawRuz(gregorianYear) {
    // Naw-Rúz falls on March 20 or 21 depending on the spring equinox
    // From 2015 onwards, we use March 20 (simplified)
    return new Date(gregorianYear, 2, gregorianYear >= 2015 ? 20 : 21);
}

function isLeapYearBadi(badiYear) {
    // Check if the Badí' year is a leap year (5 Ayyám-i-Há days instead of 4)
    const gregorianYear = badiYear + 1843;
    const nextYear = gregorianYear + 1;
    return (nextYear % 4 === 0 && nextYear % 100 !== 0) || (nextYear % 400 === 0);
}

function gregorianToBadi(gregorianDate) {
    const date = new Date(gregorianDate);
    
    // Handle invalid dates
    if (isNaN(date.getTime())) {
        return { year: 0, month: 1, day: 1 };
    }
    
    const nawRuzThisYear = getNawRuz(date.getFullYear());
    
    let badiYear, startOfYear;
    if (date >= nawRuzThisYear) {
        badiYear = date.getFullYear() - 1843;
        startOfYear = nawRuzThisYear;
    } else {
        badiYear = date.getFullYear() - 1844;
        startOfYear = getNawRuz(date.getFullYear() - 1);
    }
    
    // Calculate day of the Badí' year (1-indexed)
    const dayOfYear = Math.floor((date - startOfYear) / (1000 * 60 * 60 * 24)) + 1;
    
    // Safety check for dayOfYear
    if (dayOfYear < 1) {
        return { year: badiYear, month: 1, day: 1 };
    }
    
    let month, day;
    if (dayOfYear <= 342) {  // First 18 months (18 * 19 = 342 days)
        month = Math.floor((dayOfYear - 1) / 19) + 1;
        day = ((dayOfYear - 1) % 19) + 1;
    } else {
        const ayyamDays = isLeapYearBadi(badiYear) ? 5 : 4;
        if (dayOfYear <= 342 + ayyamDays) {
            // Ayyám-i-Há
            month = 0;
            day = dayOfYear - 342;
        } else {
            // Month of 'Alá' (19th month)
            month = 19;
            day = dayOfYear - 342 - ayyamDays;
        }
    }
    
    return { year: badiYear, month: month, day: day };
}

function badiToGregorian(badiYear, badiMonth, badiDay) {
    const gregorianYear = badiYear + 1843;
    const nawRuz = getNawRuz(gregorianYear);
    
    let dayOfYear;
    if (badiMonth >= 1 && badiMonth <= 18) {
        dayOfYear = (badiMonth - 1) * 19 + badiDay;
    } else if (badiMonth === 0) {
        dayOfYear = 342 + badiDay;
    } else if (badiMonth === 19) {
        const ayyamDays = isLeapYearBadi(badiYear) ? 5 : 4;
        dayOfYear = 342 + ayyamDays + badiDay;
    } else {
        throw new Error(`Invalid Badí' month: ${badiMonth}`);
    }
    
    const result = new Date(nawRuz);
    result.setDate(result.getDate() + dayOfYear - 1);
    return result;
}

function getBadiMonthName(monthNumber) {
    const month = BADI_MONTHS.find(m => m.number === monthNumber);
    return month ? month.name : 'Unknown';
}

function formatBadiDate(badiYear, badiMonth, badiDay) {
    const monthName = getBadiMonthName(badiMonth);
    return `${badiDay} ${monthName} ${badiYear} BE`;
}

function getCurrentBadiDate() {
    return gregorianToBadi(new Date());
}

function getGregorianYearFromBadi(badiYear, badiMonth) {
    // Convert Badí' year and month to approximate Gregorian year
    if (badiMonth >= 1 && badiMonth <= 18) {
        return badiYear + 1843;
    }
    return badiYear + 1844;  // For 'Alá' and Ayyám-i-Há (in Feb/Mar of next Gregorian year)
}

// Get Gregorian date range for a Bahá'í month
function getBadiMonthDateRange(badiYear, badiMonth) {
    let startDate, endDate;
    
    if (badiMonth >= 1 && badiMonth <= 18) {
        // Regular months (19 days each)
        startDate = badiToGregorian(badiYear, badiMonth, 1);
        endDate = badiToGregorian(badiYear, badiMonth, 19);
    } else if (badiMonth === 0) {
        // Ayyám-i-Há (intercalary days)
        const ayyamDays = isLeapYearBadi(badiYear) ? 5 : 4;
        startDate = badiToGregorian(badiYear, 0, 1);
        endDate = badiToGregorian(badiYear, 0, ayyamDays);
    } else if (badiMonth === 19) {
        // 'Alá' (month of fasting)
        startDate = badiToGregorian(badiYear, 19, 1);
        endDate = badiToGregorian(badiYear, 19, 19);
    }
    
    return { start: startDate, end: endDate };
}

// Get Gregorian date range for an entire Bahá'í year
function getBadiYearDateRange(badiYear) {
    // Bahá'í year starts at Naw-Rúz (March 20/21) of the corresponding Gregorian year
    // and ends the day before the next Naw-Rúz
    const gregorianYear = badiYear + 1843;
    const startDate = getNawRuz(gregorianYear);
    
    // End date is the day before next Naw-Rúz
    const nextNawRuz = getNawRuz(gregorianYear + 1);
    const endDate = new Date(nextNawRuz);
    endDate.setDate(endDate.getDate() - 1);
    
    return { start: startDate, end: endDate };
}

// Fetch wrapper to always include credentials
async function apiFetch(url, options = {}) {
    const defaultOptions = {
        credentials: 'include'
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    // Handle authentication errors
    if (response.status === 401) {
        // Session expired, redirect to login
        state.isAuthenticated = false;
        state.currentUser = null;
        showLoginScreen();
        throw new Error('Session expired. Please login again.');
    }
    
    return response;
}

// State Management
const state = {
    currentPage: 'dashboard',
    period: 'monthly',
    calendarType: 'gregorian',  // 'gregorian' or 'badi'
    badiYear: null,
    badiMonth: null,
    transactions: [],
    categories: [],
    budgets: [],
    filters: {
        category: null,
        type: null
    },
    currentTransaction: null,
    charts: {},
    sortConfig: {
        field: 'date',
        direction: 'desc'
    },
    currentUser: null,
    isAuthenticated: false
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOMContentLoaded event fired');
    
    // Check authentication first
    await checkAuth();
    
    if (!state.isAuthenticated) {
        showLoginScreen();
        initializeLoginListeners();
        return;
    }
    
    // User is authenticated, show main app
    showMainApp();
});

// Authentication Functions
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
                state.isAuthenticated = true;
                state.currentUser = data.user;
                return true;
            }
        }
        
        state.isAuthenticated = false;
        state.currentUser = null;
        return false;
    } catch (error) {
        console.error('Auth check failed:', error);
        state.isAuthenticated = false;
        state.currentUser = null;
        return false;
    }
}

function showLoginScreen() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

function showMainApp() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('mainApp').style.display = 'flex';
    
    // Update user display
    updateUserDisplay();
    
    // Apply read-only mode if viewer user
    if (state.currentUser && state.currentUser.role === 'viewer') {
        document.body.classList.add('read-only');
    } else {
        document.body.classList.remove('read-only');
    }
    
    // Apply calendar preference filtering
    applyCalendarPreference();
    
    // Ensure we always start on dashboard after login
    navigateTo('dashboard');
    
    // Initialize the rest of the app
    initializeApp();
}

/**
 * Apply calendar preference to filter time frame options based on user settings
 * @param {string} preference - 'both', 'gregorian', or 'badi'
 */
function applyCalendarPreference(preference = null) {
    const calendarPref = preference || (state.currentUser && state.currentUser.calendar_preference) || 'both';
    
    // Apply to the main calendar type selector in the header
    const calendarTypeSelect = document.getElementById('calendarTypeSelect');
    if (calendarTypeSelect) {
        const gregorianOption = calendarTypeSelect.querySelector('option[value="gregorian"]');
        const badiOption = calendarTypeSelect.querySelector('option[value="badi"]');
        
        if (calendarPref === 'gregorian') {
            // Hide Badí' option, force Gregorian
            if (badiOption) {
                badiOption.style.display = 'none';
                badiOption.disabled = true;
            }
            if (gregorianOption) {
                gregorianOption.style.display = '';
                gregorianOption.disabled = false;
            }
            calendarTypeSelect.value = 'gregorian';
            toggleCalendarType('gregorian');
        } else if (calendarPref === 'badi') {
            // Hide Gregorian option, force Badí'
            if (gregorianOption) {
                gregorianOption.style.display = 'none';
                gregorianOption.disabled = true;
            }
            if (badiOption) {
                badiOption.style.display = '';
                badiOption.disabled = false;
            }
            calendarTypeSelect.value = 'badi';
            toggleCalendarType('badi');
        } else {
            // Show both options
            if (gregorianOption) {
                gregorianOption.style.display = '';
                gregorianOption.disabled = false;
            }
            if (badiOption) {
                badiOption.style.display = '';
                badiOption.disabled = false;
            }
        }
    }
    
    // All time frame type selectors in the application
    const timeFrameSelectors = [
        'csTimeFrameType',           // Charts & Summaries main selector
        'period1TimeFrameType',      // Period comparison 1
        'period2TimeFrameType'       // Period comparison 2
    ];
    
    timeFrameSelectors.forEach(selectorId => {
        const select = document.getElementById(selectorId);
        if (!select) return;
        
        // Get all options
        const options = select.querySelectorAll('option');
        
        options.forEach(option => {
            const value = option.value;
            const isGregorian = value.startsWith('gregorian') || value === 'custom';
            const isBadi = value.startsWith('badi');
            
            if (calendarPref === 'gregorian') {
                // Hide Badi options
                option.style.display = isBadi ? 'none' : '';
                option.disabled = isBadi;
            } else if (calendarPref === 'badi') {
                // Hide Gregorian options (but keep custom which works for both)
                option.style.display = (isGregorian && value !== 'custom') ? 'none' : '';
                option.disabled = (isGregorian && value !== 'custom');
            } else {
                // Show all options
                option.style.display = '';
                option.disabled = false;
            }
        });
        
        // If current selection is now hidden, reset to first visible option
        const currentOption = select.querySelector(`option[value="${select.value}"]`);
        if (currentOption && currentOption.disabled) {
            const firstVisible = select.querySelector('option:not([disabled])');
            if (firstVisible) {
                select.value = firstVisible.value;
                // Trigger change event
                select.dispatchEvent(new Event('change'));
            }
        }
    });
    
    console.log('Calendar preference applied:', calendarPref);
}

function updateUserDisplay() {
    if (state.currentUser) {
        document.getElementById('currentUserDisplay').textContent = state.currentUser.username;
        document.getElementById('dropdownUsername').textContent = state.currentUser.username;
        
        const roleBadge = document.getElementById('dropdownRole');
        const roleLabels = {'superuser': 'Super User', 'standard': 'Standard', 'viewer': 'Viewer'};
        roleBadge.textContent = roleLabels[state.currentUser.role] || state.currentUser.role;
        roleBadge.className = 'role-badge ' + state.currentUser.role;
    }
}

function initializeLoginListeners() {
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', handleLogin);
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    errorDiv.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            errorDiv.textContent = data.error || 'Login failed';
            errorDiv.style.display = 'block';
            return;
        }
        
        state.isAuthenticated = true;
        state.currentUser = data.user;
        state.currentPage = 'dashboard';  // Always start on dashboard after login
        showMainApp();
        
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.style.display = 'block';
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    state.isAuthenticated = false;
    state.currentUser = null;
    state.currentPage = 'dashboard';  // Reset to dashboard on logout
    document.body.classList.remove('read-only');
    showLoginScreen();
    
    // Clear form
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('loginError').style.display = 'none';
}

async function initializeApp() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');

    // Monthly picker — current month
    document.getElementById('monthPicker').value = `${year}-${month}`;

    // Daily picker — today
    document.getElementById('dayPicker').value = today.toISOString().split('T')[0];

    // Weekly picker — current ISO week
    const isoWeek = getISOWeek(today);
    document.getElementById('weekPicker').value = `${year}-W${String(isoWeek).padStart(2, '0')}`;

    // Annual picker — current year
    document.getElementById('yearPicker').value = year;

    // Custom range — first day of current month to today
    const firstOfMonth = `${year}-${month}-01`;
    document.getElementById('customStartDate').value = firstOfMonth;
    document.getElementById('customEndDate').value = today.toISOString().split('T')[0];

    // Initialize Badí' calendar selectors
    initializeBadiCalendar();

    // Show the right pickers for the default period (monthly)
    updateDatePickerVisibility();

    console.log('Initializing event listeners...');
    initializeEventListeners();
    console.log('Initializing categories...');
    await initializeCategories();
    console.log('Loading dashboard...');
    await loadDashboard();
    console.log('Page initialized');
}

// Return ISO week number for a Date
function getISOWeek(date) {
    const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// Initialize Badí' Calendar UI
function initializeBadiCalendar() {
    const badiMonthPicker = document.getElementById('badiMonthPicker');
    const badiYearPicker = document.getElementById('badiYearPicker');
    
    // Populate Badí' months (reorder to show chronologically)
    const monthOrder = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 0, 19];
    badiMonthPicker.innerHTML = monthOrder.map(num => {
        const month = BADI_MONTHS.find(m => m.number === num);
        return `<option value="${month.number}">${month.name} (${month.meaning})</option>`;
    }).join('');
    
    // Get current Badí' date
    const currentBadi = getCurrentBadiDate();
    state.badiYear = currentBadi.year;
    state.badiMonth = currentBadi.month;
    
    // Populate Badí' years (5 years back to current year)
    badiYearPicker.innerHTML = '';
    for (let y = currentBadi.year - 5; y <= currentBadi.year; y++) {
        const option = document.createElement('option');
        option.value = y;
        option.textContent = `${y} BE`;
        badiYearPicker.appendChild(option);
    }
    
    // Set current values
    badiMonthPicker.value = currentBadi.month;
    badiYearPicker.value = currentBadi.year;
}

// Toggle between Gregorian and Badí' calendar UI
function toggleCalendarType(type) {
    state.calendarType = type;
    updateDatePickerVisibility();
    // Don't auto-load - wait for Apply button
}

// Show/hide the right date pickers based on current period and calendar type
function updateDatePickerVisibility() {
    const period = document.getElementById('periodSelect').value;
    const calType = document.getElementById('calendarTypeSelect').value;
    const isBadi = calType === 'badi';

    // All pickers to manage
    const pickers = {
        dayPicker: false,
        weekPicker: false,
        monthPicker: false,
        yearPicker: false,
        customStartDate: false,
        customRangeSep: false,
        customEndDate: false,
        badiMonthPicker: false,
        badiYearPicker: false
    };

    if (period === 'custom') {
        pickers.customStartDate = true;
        pickers.customRangeSep = true;
        pickers.customEndDate = true;
    } else if (period === 'daily') {
        pickers.dayPicker = true;   // Gregorian day picker works for both
    } else if (period === 'weekly') {
        pickers.weekPicker = true;  // ISO week picker works for both
    } else if (period === 'monthly') {
        if (isBadi) {
            pickers.badiMonthPicker = true;
            pickers.badiYearPicker = true;
        } else {
            pickers.monthPicker = true;
        }
    } else if (period === 'annual') {
        if (isBadi) {
            pickers.badiYearPicker = true;
        } else {
            pickers.yearPicker = true;
        }
    }

    Object.entries(pickers).forEach(([id, visible]) => {
        const el = document.getElementById(id);
        if (el) el.style.display = visible ? (id === 'customRangeSep' ? 'flex' : 'block') : 'none';
    });
}

// Convert ISO week string 'YYYY-Www' to the Monday date string 'YYYY-MM-DD'
function weekValueToMonday(weekValue) {
    const [yearStr, weekStr] = weekValue.split('-W');
    const year = parseInt(yearStr);
    const week = parseInt(weekStr);
    // ISO week 1 = week containing Jan 4
    const jan4 = new Date(year, 0, 4);
    const jan4Day = jan4.getDay() || 7;  // convert Sun=0 to 7
    const monday = new Date(jan4.getTime() - (jan4Day - 1) * 86400000 + (week - 1) * 7 * 86400000);
    return monday.toISOString().split('T')[0];
}

// Build URLSearchParams for report/summary/budget API calls
function getDateParams() {
    const params = new URLSearchParams();
    const period = state.period;
    const calType = state.calendarType;

    params.append('period', period);
    params.append('calendar', calType);

    if (period === 'custom') {
        const start = document.getElementById('customStartDate').value;
        const end   = document.getElementById('customEndDate').value;
        if (start) params.append('date_from', start);
        if (end)   params.append('date_to', end);
    } else if (period === 'daily') {
        const val = document.getElementById('dayPicker').value;
        if (val) params.append('specific_date', val);
    } else if (period === 'weekly') {
        const weekVal = document.getElementById('weekPicker').value;
        if (weekVal) params.append('week_start', weekValueToMonday(weekVal));
    } else if (period === 'monthly') {
        if (calType === 'badi') {
            params.append('year', state.badiYear);
            params.append('month', state.badiMonth);
        } else {
            const val = document.getElementById('monthPicker').value;
            if (val) { const [y, m] = val.split('-'); params.append('year', y); params.append('month', m); }
        }
    } else if (period === 'annual') {
        if (calType === 'badi') {
            params.append('year', state.badiYear);
        } else {
            const val = document.getElementById('yearPicker').value;
            if (val) params.append('year', val);
        }
    }
    return params;
}

// Compute {start, end} date strings for the transactions endpoint
function getDateRange() {
    const period = state.period;
    const calType = state.calendarType;
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];

    if (period === 'custom') {
        return {
            start: document.getElementById('customStartDate').value || todayStr,
            end:   document.getElementById('customEndDate').value   || todayStr
        };
    }
    if (period === 'daily') {
        const v = document.getElementById('dayPicker').value || todayStr;
        return { start: v, end: v };
    }
    if (period === 'weekly') {
        const weekVal = document.getElementById('weekPicker').value;
        let mondayStr;
        if (weekVal) {
            mondayStr = weekValueToMonday(weekVal);
        } else {
            const d = new Date(today);
            const day = d.getDay() || 7;
            d.setDate(d.getDate() - (day - 1));
            mondayStr = d.toISOString().split('T')[0];
        }
        const sun = new Date(mondayStr);
        sun.setDate(sun.getDate() + 6);
        return { start: mondayStr, end: sun.toISOString().split('T')[0] };
    }
    if (period === 'monthly') {
        if (calType === 'badi') {
            const range = getBadiMonthDateRange(state.badiYear, state.badiMonth);
            return {
                start: range.start.toISOString().split('T')[0],
                end:   range.end.toISOString().split('T')[0]
            };
        }
        const val = document.getElementById('monthPicker').value;
        const y = val ? parseInt(val.split('-')[0]) : today.getFullYear();
        const m = val ? parseInt(val.split('-')[1]) : today.getMonth() + 1;
        const first = `${y}-${String(m).padStart(2, '0')}-01`;
        const last  = `${y}-${String(m).padStart(2, '0')}-${String(new Date(y, m, 0).getDate()).padStart(2, '0')}`;
        return { start: first, end: last };
    }
    if (period === 'annual') {
        if (calType === 'badi') {
            const range = getBadiYearDateRange(state.badiYear);
            const endStr = range.end.toISOString().split('T')[0];
            return {
                start: range.start.toISOString().split('T')[0],
                end:   endStr > todayStr ? todayStr : endStr
            };
        }
        const yr = parseInt(document.getElementById('yearPicker').value) || today.getFullYear();
        const start = `${yr}-01-01`;
        const end   = yr < today.getFullYear() ? `${yr}-12-31` : todayStr;
        return { start, end };
    }
    return null;
}

// Human-readable label for the current period selection
function getPeriodLabel() {
    const period = state.period;
    if (period === 'daily') {
        return document.getElementById('dayPicker').value || 'Today';
    } else if (period === 'weekly') {
        const wv = document.getElementById('weekPicker').value;
        return wv ? `Week of ${weekValueToMonday(wv)}` : 'This Week';
    } else if (period === 'monthly') {
        return document.getElementById('monthPicker').value || 'This Month';
    } else if (period === 'annual') {
        return document.getElementById('yearPicker').value || String(new Date().getFullYear());
    } else if (period === 'custom') {
        const s = document.getElementById('customStartDate').value;
        const e = document.getElementById('customEndDate').value;
        return s && e ? `${s} → ${e}` : 'Custom';
    }
    return period;
}

// Apply calendar settings and reload whatever page is active
function applyCalendarSettings() {
    state.calendarType = document.getElementById('calendarTypeSelect').value;
    state.period = document.getElementById('periodSelect').value;

    if (state.calendarType === 'badi') {
        state.badiMonth = parseInt(document.getElementById('badiMonthPicker').value);
        state.badiYear  = parseInt(document.getElementById('badiYearPicker').value);
    }

    // Reset transaction sort to date descending whenever a date filter is applied
    state.sortConfig = { field: 'date', direction: 'desc' };

    // Reload data for whichever page is currently active
    switch (state.currentPage) {
        case 'dashboard':     loadDashboard();     break;
        case 'transactions':  loadTransactions();  break;
        case 'budgets':       loadBudgets();       break;
        case 'reports':       loadReports();       break;
        case 'charts-summaries': loadChartsSummaries(); break;
        default:              loadDashboard();     break;
    }

    showNotification('Date filter applied', 'success');
}

// Event Listeners
function initializeEventListeners() {
    // Navigation
    console.log('Setting up navigation event listeners...');
    const navLinks = document.querySelectorAll('.nav-link');
    console.log('Found nav links:', navLinks.length);
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;
            console.log('Nav link clicked:', page);
            
            // Handle submenu toggle for parent items
            const parentLi = link.closest('.has-submenu');
            if (parentLi && !link.classList.contains('sub-link')) {
                // Toggle submenu expansion
                parentLi.classList.toggle('expanded');
            }
            
            navigateTo(page);
        });
    });

    // Period selector
    document.getElementById('periodSelect').addEventListener('change', (e) => {
        state.period = e.target.value;
        updateDatePickerVisibility();
        // Don't auto-load - wait for Apply button
    });

    document.getElementById('monthPicker').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });
    document.getElementById('dayPicker').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });
    document.getElementById('weekPicker').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });
    document.getElementById('yearPicker').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });
    document.getElementById('customStartDate').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });
    document.getElementById('customEndDate').addEventListener('change', () => {
        // Don't auto-load - wait for Apply button
    });

    // Calendar type selector
    document.getElementById('calendarTypeSelect').addEventListener('change', (e) => {
        toggleCalendarType(e.target.value);
        // Don't auto-load - wait for Apply button
    });

    // Badí' calendar selectors
    document.getElementById('badiMonthPicker').addEventListener('change', (e) => {
        state.badiMonth = parseInt(e.target.value);
        // Don't auto-load - wait for Apply button
    });

    document.getElementById('badiYearPicker').addEventListener('change', (e) => {
        state.badiYear = parseInt(e.target.value);
        // Don't auto-load - wait for Apply button
    });

    // Apply Calendar Button
    document.getElementById('applyCalendarBtn').addEventListener('click', () => {
        applyCalendarSettings();
    });

    // Transaction modal
    document.getElementById('addTransBtn').addEventListener('click', () => {
        state.currentTransaction = null;
        document.getElementById('modalTitle').textContent = 'Add Transaction';
        document.getElementById('transactionForm').reset();
        document.getElementById('statusGroup').style.display = 'none';
        openModal('transactionModal');
    });

    document.getElementById('transactionForm').addEventListener('submit', handleTransactionSubmit);

    // Category modal (from transaction form)
    document.getElementById('addCategoryBtn').addEventListener('click', () => {
        openCategoryModal();
        // Pre-select the type based on current transaction type selection
        const transType = document.getElementById('transType').value;
        if (transType) {
            document.getElementById('categoryType').value = transType;
        }
    });

    // Category page add button
    document.getElementById('addCategoryPageBtn').addEventListener('click', () => {
        openCategoryModal();
    });

    document.getElementById('categoryForm').addEventListener('submit', handleCategorySubmit);

    // Budget modal
    document.getElementById('addBudgetBtn').addEventListener('click', () => {
        openModal('budgetModal');
    });

    document.getElementById('budgetForm').addEventListener('submit', handleBudgetSubmit);

    // Rules
    document.getElementById('addRuleBtn').addEventListener('click', () => {
        document.getElementById('ruleForm').reset();
        delete document.getElementById('ruleForm').dataset.ruleId;
        document.getElementById('ruleModalTitle').textContent = 'Add Categorization Rule';
        openModal('ruleModal');
    });

    document.getElementById('ruleForm').addEventListener('submit', handleRuleSubmit);
    document.getElementById('ruleTestInput').addEventListener('input', testRule);
    document.getElementById('applyRulesBtn').addEventListener('click', applyRulesToAllTransactions);
    document.getElementById('exportRulesBtn').addEventListener('click', exportRules);
    document.getElementById('importRulesBtn').addEventListener('click', () => {
        document.getElementById('importRulesFile').click();
    });
    document.getElementById('importRulesFile').addEventListener('change', handleRulesImport);

    // User Menu
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (userDropdown) userDropdown.classList.remove('show');
    });
    
    // Logout
    const logoutLink = document.getElementById('logoutLink');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            handleLogout();
        });
    }
    
    // Change Password
    const changePasswordLink = document.getElementById('changePasswordLink');
    if (changePasswordLink) {
        changePasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            userDropdown.classList.remove('show');
            openModal('changePasswordModal');
        });
    }
    
    // Change Password Form
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', handleChangePassword);
    }
    
    // Add User Button (in settings)
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', () => {
            openUserModal();
        });
    }
    
    // User Form
    const userForm = document.getElementById('userForm');
    if (userForm) {
        userForm.addEventListener('submit', handleUserSubmit);
    }

    // API Status Toggle
    const apiToggle = document.getElementById('apiToggle');
    if (apiToggle) {
        apiToggle.addEventListener('change', handleApiToggle);
    }

    // Initialize Clear Transactions functionality
    initializeClearTransactions();

    // Initialize Upload History listeners
    initializeUploadHistoryListeners();

    // Initialize Activity Logs listeners
    initializeActivityLogsListeners();

    // Filters
    document.getElementById('typeFilter').addEventListener('change', loadTransactions);
    document.getElementById('categoryFilter').addEventListener('change', loadTransactions);
    document.getElementById('statusFilter').addEventListener('change', loadTransactions);
    document.getElementById('budgetTypeFilter').addEventListener('change', loadBudgets);

    // Search
    document.getElementById('searchInput').addEventListener('input', filterTransactions);

    // Bulk delete by selection
    document.getElementById('bulkDeleteFileBtn').addEventListener('click', () => {
        document.getElementById('bulkDeleteFile').click();
    });

    document.getElementById('bulkDeleteFile').addEventListener('change', handleBulkDeleteFileUpload);

    // Upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#27ae60';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#3498db';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        handleFileSelect(e.dataTransfer.files);
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files));

    document.getElementById('confirmUploadBtn').addEventListener('click', confirmUpload);
    document.getElementById('cancelUploadBtn').addEventListener('click', resetUploadUI);
    document.getElementById('cancelUploadBtn').style.display = 'none';

    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').classList.remove('show');
        });
    });

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
        }
    });

    // Menu toggle for mobile sidebar
    document.getElementById('menuToggle').addEventListener('click', () => {
        toggleMobileSidebar();
    });
    
    // Close sidebar when clicking overlay
    document.getElementById('sidebarOverlay').addEventListener('click', () => {
        closeMobileSidebar();
    });
    
    // Close sidebar via close button
    document.getElementById('sidebarClose').addEventListener('click', () => {
        closeMobileSidebar();
    });
}

// Mobile sidebar functions
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
    document.body.classList.toggle('sidebar-open');
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.remove('show');
    overlay.classList.remove('show');
    document.body.classList.remove('sidebar-open');
}

// Navigation
function navigateTo(page) {
    console.log('Navigating to:', page);
    
    // Close mobile sidebar when navigating
    closeMobileSidebar();
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === page) {
            link.classList.add('active');
            // Expand parent submenu if this is a sub-link
            const parentSubmenu = link.closest('.has-submenu');
            if (parentSubmenu) {
                parentSubmenu.classList.add('expanded');
            }
        }
    });

    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'transactions': 'Transactions',
        'categories': 'Categories',
        'budgets': 'Budgets',
        'reports': 'Reports',
        'rules': 'Categorization Rules',
        'upload': 'Upload Bank Statement',
        'settings': 'Settings'
    };
    document.getElementById('pageTitle').textContent = titles[page] || 'Dashboard';

    // Show/hide pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const pageElement = document.getElementById(page);
    if (pageElement) {
        pageElement.classList.add('active');
        console.log('Page element found and activated:', page);
    } else {
        console.error('Page element not found:', page);
        return;
    }

    state.currentPage = page;

    // Load page content
    switch(page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'categories':
            loadCategoryManagement();
            break;
        case 'budgets':
            loadBudgets();
            break;
        case 'rules':
            loadRules();
            break;
        case 'reports':
            loadReports();
            break;
        case 'charts-summaries':
            loadChartsSummaries();
            break;
        case 'upload':
            loadUploadHistory();
            break;
        case 'settings':
            loadApiStatus();
            loadUsers();
            loadActivityLogs();
            break;
    }
}

// Initialize Categories
async function initializeCategories() {
    try {
        const response = await apiFetch(`${API_URL}/categories/init`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to initialize categories');
        
        await loadCategories();
    } catch (error) {
        console.error('Error initializing categories:', error);
    }
}

// Load Categories
async function loadCategories() {
    try {
        const response = await apiFetch(`${API_URL}/categories/?include_subcategories=true`, {
            credentials: 'include'
        });
        if (!response.ok) throw new Error('Failed to load categories');
        
        const allCategories = await response.json();
        state.categories = allCategories;
        
        // Build flat list with optgroup structure for dropdowns
        // Filter to parent categories only, with subcategories nested
        const parentCategories = allCategories.filter(c => !c.parent_id);
        
        // Update category filters
        const categoryFilters = ['categoryFilter', 'transCategory', 'budgetCategory', 'budgetTypeFilter', 'ruleCategory'];
        categoryFilters.forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                const currentValue = filter.value;
                filter.innerHTML = '<option value="">Select...</option>';
                
                const categories = filterId.includes('Budget') ? 
                    parentCategories.filter(c => c.type === 'expense') : 
                    parentCategories;
                
                categories.forEach(cat => {
                    // Add parent category
                    const option = document.createElement('option');
                    option.value = cat.id;
                    option.textContent = cat.name;
                    filter.appendChild(option);
                    
                    // Add subcategories with indentation
                    if (cat.subcategories && cat.subcategories.length > 0) {
                        cat.subcategories.forEach(sub => {
                            const subOption = document.createElement('option');
                            subOption.value = sub.id;
                            subOption.textContent = `  └ ${sub.name}`;
                            subOption.style.paddingLeft = '20px';
                            filter.appendChild(subOption);
                        });
                    }
                });
                
                filter.value = currentValue;
            }
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Load Category Management (for Categories page)
async function loadCategoryManagement() {
    try {
        const response = await apiFetch(`${API_URL}/categories/?include_subcategories=true`);
        if (!response.ok) throw new Error('Failed to load categories');
        
        const categories = await response.json();
        
        // Filter to parent categories only (no parent_id)
        const expenseCategories = categories.filter(c => c.type === 'expense' && !c.parent_id);
        const incomeCategories = categories.filter(c => c.type === 'income' && !c.parent_id);
        
        // Helper function to render category with subcategories
        const renderCategory = (cat) => {
            const subcategories = cat.subcategories || [];
            return `
                <li class="category-item ${cat.is_default ? 'is-default' : ''}" data-id="${cat.id}">
                    <div class="category-main">
                        <div class="category-info">
                            <span class="category-color" style="background: ${cat.color || '#3498db'}"></span>
                            <span class="category-name">${cat.name}</span>
                            ${cat.is_default ? '<span class="default-badge">Default</span>' : ''}
                        </div>
                        <div class="category-actions">
                            <button class="btn-icon" title="Add Subcategory" onclick="openSubcategoryModal(${cat.id}, '${cat.name.replace(/'/g, "\\'")}', '${cat.type}')">
                                <i class="fas fa-plus"></i>
                            </button>
                            ${!cat.is_default ? `
                                <button class="btn-icon" title="Set as Default" onclick="setCategoryDefault(${cat.id})">
                                    <i class="fas fa-star"></i>
                                </button>
                            ` : ''}
                            <button class="btn-icon edit" title="Edit" onclick="editCategory(${cat.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            ${!cat.is_default ? `
                                <button class="btn-icon delete" title="Delete" onclick="deleteCategory(${cat.id}, '${cat.name.replace(/'/g, "\\'")}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    ${subcategories.length > 0 ? `
                        <ul class="subcategory-list">
                            ${subcategories.map(sub => `
                                <li class="subcategory-item" data-id="${sub.id}">
                                    <div class="category-info">
                                        <span class="category-color" style="background: ${sub.color || cat.color || '#3498db'}"></span>
                                        <span class="category-name">${sub.name}</span>
                                    </div>
                                    <div class="category-actions">
                                        <button class="btn-icon edit" title="Edit" onclick="editCategory(${sub.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn-icon delete" title="Delete" onclick="deleteSubcategoryFromModal(${sub.id}, '${sub.name.replace(/'/g, "\\'")}')">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </li>
                            `).join('')}
                        </ul>
                    ` : ''}
                </li>
            `;
        };
        
        // Render expense categories
        const expenseList = document.getElementById('expenseCategoryList');
        if (expenseList) {
            expenseList.innerHTML = expenseCategories.map(renderCategory).join('');
        }
        
        // Render income categories
        const incomeList = document.getElementById('incomeCategoryList');
        if (incomeList) {
            incomeList.innerHTML = incomeCategories.map(renderCategory).join('');
        }
    } catch (error) {
        console.error('Error loading category management:', error);
    }
}

// Open Subcategory Modal
function openSubcategoryModal(parentId, parentName, parentType) {
    document.getElementById('categoryForm').reset();
    document.getElementById('categoryId').value = '';
    document.getElementById('categoryParentId').value = parentId;
    
    document.getElementById('categoryModalTitle').textContent = `Add Subcategory to ${parentName}`;
    document.getElementById('categorySubmitBtn').textContent = 'Create Subcategory';
    document.getElementById('categoryTypeGroup').style.display = 'none';
    document.getElementById('categoryType').value = parentType;
    
    openModal('categoryModal');
}

// Open Category Modal (for create or edit)
function openCategoryModal(category = null) {
    document.getElementById('categoryForm').reset();
    document.getElementById('categoryId').value = '';
    document.getElementById('categoryParentId').value = '';
    document.getElementById('subcategoriesSection').style.display = 'none';
    document.getElementById('subcategoriesList').innerHTML = '';
    document.getElementById('newSubcategoryName').value = '';
    
    if (category) {
        // Edit mode
        const isSubcategory = category.parent_id !== null && category.parent_id !== undefined;
        document.getElementById('categoryModalTitle').textContent = isSubcategory ? 'Edit Subcategory' : 'Edit Category';
        document.getElementById('categorySubmitBtn').textContent = 'Save Changes';
        document.getElementById('categoryId').value = category.id;
        document.getElementById('categoryName').value = category.name;
        document.getElementById('categoryType').value = category.type;
        document.getElementById('categoryColor').value = category.color || '#3498db';
        // Disable type change for existing categories
        document.getElementById('categoryTypeGroup').style.display = 'none';
        
        // Show subcategories section only for parent categories (not subcategories)
        if (!isSubcategory) {
            document.getElementById('subcategoriesSection').style.display = 'block';
            renderSubcategoriesInModal(category.subcategories || []);
        }
    } else {
        // Create mode
        document.getElementById('categoryModalTitle').textContent = 'Add New Category';
        document.getElementById('categorySubmitBtn').textContent = 'Create Category';
        document.getElementById('categoryTypeGroup').style.display = 'block';
    }
    
    openModal('categoryModal');
}

// Render subcategories in the edit modal
function renderSubcategoriesInModal(subcategories) {
    const list = document.getElementById('subcategoriesList');
    if (subcategories.length === 0) {
        list.innerHTML = '<p class="no-subcategories">No subcategories yet</p>';
        return;
    }
    
    list.innerHTML = subcategories.map(sub => `
        <div class="subcategory-edit-item" data-id="${sub.id}">
            <span class="subcategory-edit-name">${sub.name}</span>
            <button type="button" class="btn-icon delete" title="Delete subcategory" onclick="deleteSubcategoryFromModal(${sub.id}, '${sub.name.replace(/'/g, "\\'")}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Add subcategory inline from the edit modal
async function addSubcategoryInline() {
    const name = document.getElementById('newSubcategoryName').value.trim();
    const parentId = document.getElementById('categoryId').value;
    
    if (!name) {
        alert('Please enter a subcategory name');
        return;
    }
    
    if (!parentId) {
        alert('Please save the category first before adding subcategories');
        return;
    }
    
    try {
        const response = await apiFetch(`${API_URL}/categories/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parent_id: parseInt(parentId) })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create subcategory');
        }
        
        // Clear the input
        document.getElementById('newSubcategoryName').value = '';
        
        // Reload the category to get updated subcategories
        const catResponse = await apiFetch(`${API_URL}/categories/?include_subcategories=true`);
        const categories = await catResponse.json();
        const updatedCategory = categories.find(c => c.id === parseInt(parentId));
        
        if (updatedCategory) {
            renderSubcategoriesInModal(updatedCategory.subcategories || []);
        }
        
        // Also refresh the main categories list
        await loadCategories();
        if (state.currentPage === 'categories') {
            loadCategoryManagement();
        }
    } catch (error) {
        console.error('Error adding subcategory:', error);
        alert(error.message);
    }
}

// Delete subcategory from the edit modal
async function deleteSubcategoryFromModal(id, name) {
    if (!confirm(`Delete subcategory "${name}"?\n\nTransactions using this subcategory will be moved to the parent category.`)) {
        return;
    }
    
    try {
        const response = await apiFetch(`${API_URL}/categories/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete subcategory');
        }
        
        // Remove from the list
        const item = document.querySelector(`.subcategory-edit-item[data-id="${id}"]`);
        if (item) item.remove();
        
        // Check if list is now empty
        const list = document.getElementById('subcategoriesList');
        if (list.children.length === 0) {
            list.innerHTML = '<p class="no-subcategories">No subcategories yet</p>';
        }
        
        // Refresh categories
        await loadCategories();
        if (state.currentPage === 'categories') {
            loadCategoryManagement();
        }
    } catch (error) {
        console.error('Error deleting subcategory:', error);
        alert(error.message);
    }
}

// Edit Category
async function editCategory(id) {
    try {
        const response = await apiFetch(`${API_URL}/categories/?include_subcategories=true`);
        if (!response.ok) throw new Error('Failed to load categories');
        
        const categories = await response.json();
        const category = categories.find(c => c.id === id);
        
        if (category) {
            openCategoryModal(category);
        }
    } catch (error) {
        console.error('Error loading category:', error);
        alert('Error loading category');
    }
}

// Set Category as Default
async function setCategoryDefault(id) {
    try {
        const response = await apiFetch(`${API_URL}/categories/${id}/set-default`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to set default category');
        }
        
        const result = await response.json();
        
        // Reload categories everywhere
        await loadCategories();
        loadCategoryManagement();
    } catch (error) {
        console.error('Error setting default category:', error);
        alert(error.message);
    }
}

// Delete Category (handles both categories and subcategories)
async function deleteCategory(id, name, isSubcategory = false) {
    // Check if this is a subcategory by looking it up
    const category = state.categories.find(c => c.id === id);
    const isSub = isSubcategory || (category && category.parent_id);
    
    let confirmMessage;
    if (isSub) {
        confirmMessage = `Are you sure you want to delete the subcategory "${name}"?\n\nAll transactions using this subcategory will be moved to the parent category.`;
    } else {
        confirmMessage = `Are you sure you want to delete the category "${name}"?\n\nAll subcategories will also be deleted.\nAll transactions, budgets, and rules will be reassigned to the system default category.`;
    }
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await apiFetch(`${API_URL}/categories/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete category');
        }
        
        const result = await response.json();
        
        let message = `${isSub ? 'Subcategory' : 'Category'} "${name}" deleted successfully.`;
        if (result.reassigned) {
            const { transactions, budgets, rules } = result.reassigned;
            const targetCategory = result.reassigned_to || 'Other';
            if (transactions > 0 || budgets > 0 || rules > 0) {
                message += `\n\nReassigned to "${targetCategory}":`;
                if (transactions > 0) message += `\n• ${transactions} transaction(s)`;
                if (budgets > 0) message += `\n• ${budgets} budget(s)`;
                if (rules > 0) message += `\n• ${rules} rule(s)`;
            }
        }
        
        alert(message);
        
        // Reload categories everywhere
        await loadCategories();
        loadCategoryManagement();
    } catch (error) {
        console.error('Error deleting category:', error);
        alert(error.message);
    }
}

// Handle Category Submit (Create or Edit)
async function handleCategorySubmit(e) {
    e.preventDefault();
    
    const categoryId = document.getElementById('categoryId').value;
    const parentId = document.getElementById('categoryParentId').value;
    const name = document.getElementById('categoryName').value.trim();
    const type = document.getElementById('categoryType').value;
    const color = document.getElementById('categoryColor').value;
    
    // For new parent categories, type is required (subcategories inherit from parent)
    if (!name || (!categoryId && !type && !parentId)) {
        alert('Please fill all required fields');
        return;
    }
    
    try {
        let url, method, body;
        
        if (categoryId) {
            // Edit mode
            url = `${API_URL}/categories/${categoryId}`;
            method = 'PUT';
            body = { name, color };
        } else {
            // Create mode
            url = `${API_URL}/categories/`;
            method = 'POST';
            body = { name, color };
            if (parentId) {
                body.parent_id = parseInt(parentId);
            } else {
                body.type = type;
            }
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save category');
        }
        
        const savedCategory = await response.json();
        
        // Close the category modal
        closeModal('categoryModal');
        document.getElementById('categoryForm').reset();
        
        // Reload categories everywhere
        await loadCategories();
        
        // Reload category management if on that page
        if (state.currentPage === 'categories') {
            loadCategoryManagement();
        }
        
        // If we're creating from transaction form, select the new category
        if (!categoryId && document.getElementById('transCategory')) {
            document.getElementById('transCategory').value = savedCategory.id;
        }
        
        alert(`Category "${name}" ${categoryId ? 'updated' : 'created'} successfully!`);
    } catch (error) {
        console.error('Error saving category:', error);
        alert(error.message);
    }
}

// Load Dashboard
async function loadDashboard() {
    if (state.currentPage !== 'dashboard') return;

    try {
        const params = getDateParams();
        params.append('include_excluded', 'false');

        // Load summary
        const summaryResponse = await apiFetch(`${API_URL}/reports/summary?${params}`);
        const summary = await summaryResponse.json();

        document.getElementById('totalIncome').textContent   = formatCurrency(summary.total_income);
        document.getElementById('totalExpense').textContent  = formatCurrency(summary.total_expense);
        document.getElementById('netBalance').textContent    = formatCurrency(summary.net);
        document.getElementById('totalExcluded').textContent = formatCurrency(summary.total_excluded);

        // Load category breakdowns
        const [expenseResponse, incomeResponse] = await Promise.all([
            apiFetch(`${API_URL}/reports/by-category?${params}&type=expense`),
            apiFetch(`${API_URL}/reports/by-category?${params}&type=income`)
        ]);

        const expenseData = await expenseResponse.json();
        const incomeData  = await incomeResponse.json();

        updateCategoryCharts(expenseData, incomeData);
        updateCategoryBreakdown(expenseData, incomeData);

        // Load recent transactions (respect date filter)
        const dateRange = getDateRange();
        const tParams = new URLSearchParams({ include_excluded: false });
        if (dateRange) {
            tParams.append('start_date', dateRange.start);
            tParams.append('end_date',   dateRange.end);
        }
        const transResponse = await apiFetch(`${API_URL}/transactions/?${tParams}`);
        const transactions = await transResponse.json();

        const recentList = document.getElementById('recentTransList');
        recentList.innerHTML = transactions.slice(0, 5).map(t => `
            <div class="transaction-item ${t.type}">
                <div class="trans-info">
                    <div class="trans-desc">${t.description}</div>
                    <div class="trans-cat">${t.category_name} \u2022 ${formatDateWithCalendar(t.date)}</div>
                </div>
                <div class="trans-amount ${t.type}">${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Update Category Charts
function updateCategoryCharts(expenseData, incomeData) {
    const defaultColors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22'];

    // Destroy existing charts
    if (state.charts.expense) state.charts.expense.destroy();
    if (state.charts.income) state.charts.income.destroy();

    // Expense Chart
    const expenseCtx = document.getElementById('expenseChart');
    if (expenseCtx && expenseData.categories.length > 0) {
        // Use category colors if available, fallback to defaults
        const expenseColors = expenseData.categories.map((c, i) => c.color || defaultColors[i % defaultColors.length]);
        
        state.charts.expense = new Chart(expenseCtx, {
            type: 'doughnut',
            data: {
                labels: expenseData.categories.map(c => c.category),
                datasets: [{
                    data: expenseData.categories.map(c => c.amount),
                    backgroundColor: expenseColors,
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Income Chart
    const incomeCtx = document.getElementById('incomeChart');
    if (incomeCtx && incomeData.categories.length > 0) {
        // Use category colors if available, fallback to defaults
        const incomeColors = incomeData.categories.map((c, i) => c.color || defaultColors[i % defaultColors.length]);
        
        state.charts.income = new Chart(incomeCtx, {
            type: 'doughnut',
            data: {
                labels: incomeData.categories.map(c => c.category),
                datasets: [{
                    data: incomeData.categories.map(c => c.amount),
                    backgroundColor: incomeColors,
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Update Category Breakdown Tables
function updateCategoryBreakdown(expenseData, incomeData) {
    // Update Income by Category table
    const incomeBody = document.getElementById('incomeByCategory');
    if (incomeBody && incomeData.categories.length > 0) {
        const totalIncome = incomeData.categories.reduce((sum, cat) => sum + cat.amount, 0);
        incomeBody.innerHTML = incomeData.categories.map(cat => `
            <tr>
                <td>${cat.category}</td>
                <td>${formatCurrency(cat.amount)}</td>
                <td>${cat.count}</td>
                <td>${((cat.amount / totalIncome) * 100).toFixed(1)}%</td>
            </tr>
        `).join('');
    }

    // Update Expenses by Category table
    const expenseBody = document.getElementById('expenseByCategory');
    if (expenseBody && expenseData.categories.length > 0) {
        const totalExpense = expenseData.categories.reduce((sum, cat) => sum + cat.amount, 0);
        expenseBody.innerHTML = expenseData.categories.map(cat => `
            <tr>
                <td>${cat.category}</td>
                <td>${formatCurrency(cat.amount)}</td>
                <td>${cat.count}</td>
                <td>${((cat.amount / totalExpense) * 100).toFixed(1)}%</td>
                <td>${formatCurrency(cat.amount / cat.count)}</td>
            </tr>
        `).join('');
    }
}

// Load Transactions
async function loadTransactions() {
    console.log('=== loadTransactions() START ===');
    
    try {
        const typeFilterEl     = document.getElementById('typeFilter');
        const categoryFilterEl = document.getElementById('categoryFilter');
        const statusFilterEl   = document.getElementById('statusFilter');
        const transactionsBodyEl = document.getElementById('transactionsBody');
        
        console.log('DOM elements check:');
        console.log('- typeFilter:', typeFilterEl ? 'found' : 'NOT FOUND');
        console.log('- categoryFilter:', categoryFilterEl ? 'found' : 'NOT FOUND');
        console.log('- statusFilter:', statusFilterEl ? 'found' : 'NOT FOUND');
        console.log('- transactionsBody:', transactionsBodyEl ? 'found' : 'NOT FOUND');
        
        const typeFilter     = typeFilterEl     ? typeFilterEl.value     : '';
        const categoryFilter = categoryFilterEl ? categoryFilterEl.value : '';
        const statusFilter   = statusFilterEl   ? statusFilterEl.value   : '';

        const params = new URLSearchParams({ include_excluded: true });

        if (typeFilter)     params.append('type', typeFilter);
        if (categoryFilter) params.append('category_id', categoryFilter);

        // Apply the global date filter
        const dateRange = getDateRange();
        if (dateRange) {
            params.append('start_date', dateRange.start);
            params.append('end_date',   dateRange.end);
        }

        const fullUrl = `${API_URL}/transactions/?${params}`;
        console.log('Making API call to:', fullUrl);
        
        const response = await apiFetch(fullUrl);
        console.log('API Response status:', response.status);
        
        if (!response.ok) throw new Error(`Failed to load transactions: ${response.status}`);

        let transactions = await response.json();
        console.log('Raw API response - transaction count:', transactions.length);
        
        if (statusFilter === 'included') {
            transactions = transactions.filter(t => !t.is_excluded);
        } else if (statusFilter === 'excluded') {
            transactions = transactions.filter(t => t.is_excluded);
        }
        
        state.transactions = transactions;
        sortTransactions(state.sortConfig.field);
        console.log('=== loadTransactions() END ===');
    } catch (error) {
        console.error('=== ERROR in loadTransactions() ===', error);
    }
}

// Display Transactions
function displayTransactions(transactions) {
    console.log('=== displayTransactions() START ===');
    console.log('Input transactions count:', transactions ? transactions.length : 'NULL/UNDEFINED');
    console.log('Input transactions:', transactions);
    
    const tbody = document.getElementById('transactionsBody');
    console.log('transactionsBody element:', tbody);
    if (!tbody) {
        console.error('CRITICAL ERROR: transactionsBody element not found!');
        return;
    }
    
    if (!transactions || transactions.length === 0) {
        console.log('No transactions to display, setting empty HTML');
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">No transactions found</td></tr>';
        console.log('=== displayTransactions() END (empty) ===');
        return;
    }
    
    console.log('Generating HTML for', transactions.length, 'transactions...');
    
    try {
        const html = transactions.map((t, index) => {
            console.log(`Processing transaction ${index + 1}:`, t);
            return `
            <tr class="transaction-row" data-id="${t.id}">
                <td class="checkbox-col">
                    <input type="checkbox" class="transaction-checkbox" value="${t.id}" onchange="updateBulkDeleteToolbar()">
                </td>
                <td>${formatDateWithCalendar(t.date)}</td>
                <td>${escapeHtml(t.description)}</td>
                <td>${escapeHtml(t.category_name || 'Unknown')}</td>
                <td><span class="tag ${t.type}">${t.type}</span></td>
                <td class="trans-amount ${t.type}">${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}</td>
                <td><span class="tag ${t.is_excluded ? 'excluded' : 'included'}">${t.is_excluded ? 'Excluded' : 'Included'}</span></td>
                <td class="upload-date-col">${t.source === 'upload' && t.created_at ? t.created_at.substring(0, 10) : '\u2014'}</td>
                <td>
                    <div class="actions">
                        <button class="btn-icon edit" title="Edit" onclick="editTransaction(${t.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon delete" title="Delete" onclick="deleteTransaction(${t.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        }).join('');
        
        console.log('Generated HTML length:', html.length);
        console.log('Generated HTML (first 500 chars):', html.substring(0, 500));
        
        tbody.innerHTML = html;
        console.log('HTML successfully set to tbody');
        console.log('tbody.children.length after setting:', tbody.children.length);
        
    } catch (error) {
        console.error('ERROR generating HTML:', error);
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error displaying transactions</td></tr>';
    }
    
    console.log('=== displayTransactions() END ===');
}

// Sort Transactions
function sortTransactions(field) {
    console.log('=== sortTransactions() START ===');
    console.log('Sort field:', field);
    console.log('state.transactions count:', state.transactions?.length || 'NULL/UNDEFINED');
    console.log('state.transactions:', state.transactions);
    
    if (!state.transactions || state.transactions.length === 0) {
        console.log('No transactions to sort, calling displayTransactions with empty array');
        displayTransactions([]);
        console.log('=== sortTransactions() END (empty) ===');
        return;
    }
    
    // Toggle direction if clicking the same field
    if (state.sortConfig.field === field) {
        state.sortConfig.direction = state.sortConfig.direction === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortConfig.field = field;
        state.sortConfig.direction = 'asc';
    }
    
    console.log('Sort configuration:', state.sortConfig);
    
    try {
        // Sort the transactions
        const sorted = [...state.transactions].sort((a, b) => {
            let valueA, valueB;
            
            switch(field) {
                case 'date':
                    valueA = new Date(a.date);
                    valueB = new Date(b.date);
                    break;
                case 'description':
                    valueA = (a.description || '').toLowerCase();
                    valueB = (b.description || '').toLowerCase();
                    break;
                case 'category':
                    valueA = (a.category_name || '').toLowerCase();
                    valueB = (b.category_name || '').toLowerCase();
                    break;
                case 'type':
                    valueA = (a.type || '').toLowerCase();
                    valueB = (b.type || '').toLowerCase();
                    break;
                case 'amount':
                    valueA = a.amount || 0;
                    valueB = b.amount || 0;
                    break;
                case 'status':
                    valueA = a.is_excluded ? 1 : 0;
                    valueB = b.is_excluded ? 1 : 0;
                    break;
                case 'upload_date':
                    valueA = (a.source === 'upload' && a.created_at) ? new Date(a.created_at) : new Date(0);
                    valueB = (b.source === 'upload' && b.created_at) ? new Date(b.created_at) : new Date(0);
                    break;
                default:
                    return 0;
            }
            
            if (valueA < valueB) return state.sortConfig.direction === 'asc' ? -1 : 1;
            if (valueA > valueB) return state.sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
        
        console.log('Sorted transactions count:', sorted.length);
        console.log('First sorted transaction:', sorted[0]);
        
        // Update UI indicators
        document.querySelectorAll('table th.sortable').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            if (th.dataset.sortField === field) {
                th.classList.add(`sort-${state.sortConfig.direction}`);
            }
        });
        
        console.log('Calling displayTransactions with sorted data...');
        displayTransactions(sorted);
        
    } catch (error) {
        console.error('ERROR in sortTransactions:', error);
        displayTransactions([]);
    }
    
    console.log('=== sortTransactions() END ===');
}

// Filter Transactions
function filterTransactions() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = state.transactions.filter(t => 
        t.description.toLowerCase().includes(searchTerm) ||
        t.category_name.toLowerCase().includes(searchTerm)
    );
    
    // Apply current sort to filtered results
    const sorted = [...filtered].sort((a, b) => {
        let valueA, valueB;
        
        switch(state.sortConfig.field) {
            case 'date':
                valueA = new Date(a.date);
                valueB = new Date(b.date);
                break;
            case 'description':
                valueA = a.description.toLowerCase();
                valueB = b.description.toLowerCase();
                break;
            case 'category':
                valueA = a.category_name.toLowerCase();
                valueB = b.category_name.toLowerCase();
                break;
            case 'type':
                valueA = a.type.toLowerCase();
                valueB = b.type.toLowerCase();
                break;
            case 'amount':
                valueA = a.amount;
                valueB = b.amount;
                break;
            case 'status':
                valueA = a.is_excluded ? 1 : 0;
                valueB = b.is_excluded ? 1 : 0;
                break;
            case 'upload_date':
                valueA = (a.source === 'upload' && a.created_at) ? new Date(a.created_at) : new Date(0);
                valueB = (b.source === 'upload' && b.created_at) ? new Date(b.created_at) : new Date(0);
                break;
            default:
                return 0;
        }
        
        if (valueA < valueB) return state.sortConfig.direction === 'asc' ? -1 : 1;
        if (valueA > valueB) return state.sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    displayTransactions(sorted);
}

// Handle Transaction Submit
async function handleTransactionSubmit(e) {
    e.preventDefault();

    const date = document.getElementById('transDate').value;
    const description = document.getElementById('transDesc').value;
    const type = document.getElementById('transType').value;
    const categoryId = parseInt(document.getElementById('transCategory').value);
    const amount = parseFloat(document.getElementById('transAmount').value);
    const notes = document.getElementById('transNotes').value;
    const isExcluded = state.currentTransaction ? document.getElementById('transStatus').value === 'true' : false;

    if (!date || !description || !type || !categoryId || !amount) {
        alert('Please fill all required fields');
        return;
    }

    try {
        const url = state.currentTransaction ? 
            `${API_URL}/transactions/${state.currentTransaction.id}` :
            `${API_URL}/transactions/`;
        
        const method = state.currentTransaction ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date,
                description,
                type,
                category_id: categoryId,
                amount,
                notes,
                is_excluded: isExcluded
            })
        });

        if (!response.ok) throw new Error('Failed to save transaction');

        // Check if category changed on edit and prompt to apply to similar transactions
        if (state.currentTransaction && state.currentTransaction.category_id !== categoryId) {
            const similarTransactions = findSimilarTransactions(description, state.currentTransaction.id, categoryId);
            if (similarTransactions.length > 0) {
                const applyToAll = confirm(
                    `Found ${similarTransactions.length} similar transaction(s) with the same merchant.\n\n` +
                    `Would you like to apply this category to all of them?`
                );
                
                if (applyToAll) {
                    await applyBulkCategoryUpdate(similarTransactions.map(t => t.id), categoryId);
                }
            }
        }

        alert(state.currentTransaction ? 'Transaction updated!' : 'Transaction added!');
        document.getElementById('transactionModal').classList.remove('show');
        document.getElementById('transactionForm').reset();
        loadTransactions();
    } catch (error) {
        console.error('Error saving transaction:', error);
        alert('Error saving transaction');
    }
}

// Edit Transaction
async function editTransaction(id) {
    const trans = state.transactions.find(t => t.id === id);
    if (!trans) return;

    state.currentTransaction = trans;
    document.getElementById('modalTitle').textContent = 'Edit Transaction';
    document.getElementById('transDate').value = trans.date;
    document.getElementById('transDesc').value = trans.description;
    document.getElementById('transType').value = trans.type;
    document.getElementById('transCategory').value = trans.category_id;
    document.getElementById('transAmount').value = trans.amount;
    document.getElementById('transNotes').value = trans.notes || '';
    document.getElementById('transStatus').value = trans.is_excluded ? 'true' : 'false';
    document.getElementById('statusGroup').style.display = 'block';

    openModal('transactionModal');
}

// Delete Transaction
async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) return;

    try {
        const response = await apiFetch(`${API_URL}/transactions/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete transaction');

        alert('Transaction deleted!');
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transaction:', error);
        alert('Error deleting transaction');
    }
}

// Toggle Select All checkbox
function toggleSelectAll(checked) {
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = checked;
    });
    updateBulkDeleteToolbar();
}

// Update bulk delete toolbar visibility and count
function updateBulkDeleteToolbar() {
    const checkedBoxes = document.querySelectorAll('.transaction-checkbox:checked');
    const toolbar = document.getElementById('bulkDeleteToolbar');
    const count = checkedBoxes.length;
    
    if (count > 0) {
        toolbar.style.display = 'flex';
        document.getElementById('selectionCount').textContent = `${count} selected`;
        // Update select all checkbox state
        const allBoxes = document.querySelectorAll('.transaction-checkbox');
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        selectAllCheckbox.checked = checkedBoxes.length === allBoxes.length;
    } else {
        toolbar.style.display = 'none';
        document.getElementById('selectAllCheckbox').checked = false;
    }
}

// Bulk delete selected transactions
async function bulkDeleteSelected() {
    const checkedBoxes = document.querySelectorAll('.transaction-checkbox:checked');
    const ids = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    
    if (ids.length === 0) {
        alert('Please select transactions to delete');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to delete ${ids.length} transaction(s)? This cannot be undone.`);
    if (!confirmed) return;
    
    try {
        const response = await apiFetch(`${API_URL}/transactions/bulk-delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transaction_ids: ids
            })
        });

        if (!response.ok) throw new Error('Failed to delete transactions');

        alert(`Successfully deleted ${ids.length} transaction(s)`);
        clearSelection();
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transactions:', error);
        alert('Error deleting transactions');
    }
}

// Clear selection
function clearSelection() {
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateBulkDeleteToolbar();
}

// Handle file upload for bulk delete
async function handleBulkDeleteFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const formData = new FormData();
        formData.append('file', file);

        // First, get a preview of transactions to be deleted
        const previewResponse = await apiFetch(`${API_URL}/transactions/bulk-delete-preview/`, {
            method: 'POST',
            body: formData
        });

        if (!previewResponse.ok) {
            const error = await previewResponse.json();
            throw new Error(error.error || 'Failed to preview transactions to delete');
        }

        const previewData = await previewResponse.json();
        
        // Store file for later confirmation
        window.pendingDeleteFile = file;
        window.pendingDeleteTransactions = previewData.transactions;
        
        // Show preview modal
        showBulkDeletePreview(previewData.transactions);
        
    } catch (error) {
        console.error('Error previewing transactions:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Reset file input
        document.getElementById('bulkDeleteFile').value = '';
    }
}

// Show bulk delete preview in modal
function showBulkDeletePreview(transactions) {
    const count = transactions.length;
    document.getElementById('previewCount').textContent = `${count} transaction(s) will be deleted:`;
    
    const previewDiv = document.getElementById('previewTransactions');
    previewDiv.innerHTML = transactions.map(t => `
        <div style="padding: 10px; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div style="font-weight: 600;">${t.description}</div>
                <div style="font-size: 12px; color: #666;">
                    ${formatDate(t.date)} • ${t.category_name}
                </div>
            </div>
            <div style="text-align: right; font-weight: 600; color: ${t.type === 'income' ? 'var(--income)' : 'var(--expense)'};">
                ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
            </div>
        </div>
    `).join('');
    
    openModal('bulkDeletePreviewModal');
}

// Confirm bulk delete from file
async function confirmBulkDeleteFromFile() {
    if (!window.pendingDeleteFile) {
        alert('No file pending deletion');
        return;
    }
    
    const confirmed = confirm(`Are you sure you want to permanently delete ${window.pendingDeleteTransactions.length} transaction(s)? This cannot be undone.`);
    if (!confirmed) return;
    
    try {
        const formData = new FormData();
        formData.append('file', window.pendingDeleteFile);
        
        const response = await apiFetch(`${API_URL}/transactions/bulk-delete-by-file/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete transactions from file');
        }

        const result = await response.json();
        alert(`Successfully deleted ${result.deleted_count} transaction(s) from file`);
        
        // Clear pending data
        window.pendingDeleteFile = null;
        window.pendingDeleteTransactions = null;
        
        // Close modal and reload
        closeModal('bulkDeletePreviewModal');
        loadTransactions();
    } catch (error) {
        console.error('Error deleting transactions from file:', error);
        alert(`Error: ${error.message}`);
    }
}

// Update Transaction Status (from dropdown)
async function updateTransactionStatus(id, status) {
    const isExcluded = status === 'true';
    try {
        const response = await apiFetch(`${API_URL}/transactions/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_excluded: isExcluded
            })
        });

        if (!response.ok) throw new Error('Failed to update transaction status');

        loadTransactions();
    } catch (error) {
        console.error('Error updating status:', error);
        alert('Error updating transaction status');
    }
}

// Find similar transactions by merchant/description
function findSimilarTransactions(description, excludeId, categoryId) {
    const normalizedDesc = description.toLowerCase().trim();
    const merchantName = extractMerchantName(normalizedDesc);
    
    return state.transactions.filter(t => {
        // Exclude the current transaction being edited
        if (t.id === excludeId) return false;
        
        // Only include transactions that don't already have this category
        if (t.category_id === categoryId) return false;
        
        // Match by merchant name
        const tMerchant = extractMerchantName(t.description.toLowerCase().trim());
        return tMerchant === merchantName && tMerchant.length > 0;
    });
}

// Extract merchant name from description (first word or meaningful part)
function extractMerchantName(description) {
    // Remove common prefixes like "DEBIT", "TRANSFER", "PAYMENT"
    const cleanDesc = description
        .replace(/^(debit|transfer|payment|check|ach|wire|atm|pos|purchase|transaction|ref:|memo:)\s*/gi, '')
        .trim();
    
    // Get first word or first meaningful part
    const words = cleanDesc.split(/[\s\-\/]/);
    const firstWord = words[0];
    
    // Return first word if it's substantial (not a number/date)
    if (firstWord && firstWord.length > 2 && !/^\d+$/.test(firstWord)) {
        return firstWord;
    }
    return '';
}

// Apply category to multiple transactions
async function applyBulkCategoryUpdate(transactionIds, categoryId) {
    try {
        const response = await apiFetch(`${API_URL}/transactions/bulk-update/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transaction_ids: transactionIds,
                category_id: categoryId
            })
        });

        if (!response.ok) throw new Error('Failed to apply category to similar transactions');

        loadTransactions();
        alert(`Applied category to ${transactionIds.length} transaction(s)`);
    } catch (error) {
        console.error('Error applying bulk category update:', error);
        // Don't alert here since main transaction was already saved
    }
}

// Load Budgets
async function loadBudgets() {
    try {
        const dateParams = getDateParams();

        const [budgetResponse, spendingResponse] = await Promise.all([
            apiFetch(`${API_URL}/budgets/`),
            apiFetch(`${API_URL}/reports/by-category?${dateParams}&type=expense&include_excluded=false`)
        ]);

        if (!budgetResponse.ok) throw new Error('Failed to load budgets');
        state.budgets = await budgetResponse.json();

        const spendingData = spendingResponse.ok ? await spendingResponse.json() : { categories: [] };
        const spendingByCatId = {};
        spendingData.categories.forEach(c => {
            if (c.category_id != null) spendingByCatId[c.category_id] = c;
        });

        const grid = document.getElementById('budgetsGrid');
        if (state.budgets.length === 0) {
            grid.innerHTML = '<p>No budgets created yet. Create one to get started!</p>';
            return;
        }

        const periodLabel = getPeriodLabel();

        grid.innerHTML = state.budgets.map(b => {
            const spending   = spendingByCatId[b.category_id];
            const actual     = spending ? spending.amount : 0;
            const pct        = b.amount > 0 ? Math.min((actual / b.amount) * 100, 100) : 0;
            const isOver     = actual > b.amount;
            const statusCls  = isOver ? 'expense' : 'income';
            return `
            <div class="budget-card">
                <h4>${b.category_name}</h4>
                <div class="budget-info">
                    <div class="budget-row">
                        <label>Budget:</label>
                        <span class="value">${formatCurrency(b.amount)} (${b.period})</span>
                    </div>
                    <div class="budget-row">
                        <label>Spent (${escapeHtml(periodLabel)}):</label>
                        <span class="value tag ${statusCls}">${formatCurrency(actual)}</span>
                    </div>
                    <div style="margin: 8px 0;">
                        <div class="budget-progress">
                            <div class="progress-bar ${isOver ? 'over' : ''}" style="width: ${pct.toFixed(1)}%"></div>
                        </div>
                        <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">${pct.toFixed(0)}% used</div>
                    </div>
                    <div class="budget-row">
                        <label>Scope:</label>
                        <span class="value">${b.for_excluded ? 'Excluded only' : 'All expenses'}</span>
                    </div>
                </div>
                <div class="budget-actions">
                    <button class="btn btn-secondary" onclick="editBudget(${b.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-danger" onclick="deleteBudget(${b.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>`;
        }).join('');
    } catch (error) {
        console.error('Error loading budgets:', error);
    }
}

// Handle Budget Submit
async function handleBudgetSubmit(e) {
    e.preventDefault();

    const categoryId = parseInt(document.getElementById('budgetCategory').value);
    const amount = parseFloat(document.getElementById('budgetAmount').value);
    const period = document.getElementById('budgetPeriod').value;
    const forExcluded = document.getElementById('budgetExcluded').checked;

    if (!categoryId || !amount || !period) {
        alert('Please fill all required fields');
        return;
    }

    try {
        const today = new Date();
        const response = await apiFetch(`${API_URL}/budgets/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category_id: categoryId,
                amount,
                period,
                year: today.getFullYear(),
                month: today.getMonth() + 1,
                for_excluded: forExcluded
            })
        });

        if (!response.ok) throw new Error('Failed to create budget');

        alert('Budget created!');
        document.getElementById('budgetModal').classList.remove('show');
        document.getElementById('budgetForm').reset();
        loadBudgets();
    } catch (error) {
        console.error('Error creating budget:', error);
        alert('Error creating budget');
    }
}

// Delete Budget
async function deleteBudget(id) {
    if (!confirm('Are you sure you want to delete this budget?')) return;

    try {
        const response = await apiFetch(`${API_URL}/budgets/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete budget');

        alert('Budget deleted!');
        loadBudgets();
    } catch (error) {
        console.error('Error deleting budget:', error);
    }
}

// Load Reports
async function loadReports() {
    try {
        const params = getDateParams();
        params.append('include_excluded', 'false');

        // Load trending data
        const trendingResponse = await apiFetch(`${API_URL}/reports/trending?months=6&type=expense`);
        const trending = await trendingResponse.json();
        updateTrendingChart(trending);

        // Load budget analysis
        const budgetResponse = await apiFetch(`${API_URL}/reports/budget-analysis?${params}`);
        const budgetAnalysis = await budgetResponse.json();
        displayBudgetAnalysis(budgetAnalysis);

        // Load category breakdown
        const categoryResponse = await apiFetch(`${API_URL}/reports/by-category?${params}&type=expense`);
        const categoryData = await categoryResponse.json();
        displayCategoryBreakdown(categoryData);
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

// Update Trending Chart
function updateTrendingChart(data) {
    if (state.charts.trending) state.charts.trending.destroy();

    const ctx = document.getElementById('trendingChart');
    state.charts.trending = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.data.map(d => d.month),
            datasets: [{
                label: 'Monthly Expenses',
                data: data.data.map(d => d.amount),
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Display Budget Analysis
function displayBudgetAnalysis(data) {
    const container = document.getElementById('budgetAnalysisContainer');
    if (!data.budgets || data.budgets.length === 0) {
        container.innerHTML = '<p>No budgets to analyze</p>';
        return;
    }

    container.innerHTML = data.budgets.map(b => `
        <div class="category-row">
            <div>
                <div class="name">${b.category}</div>
                <div class="percent">${formatCurrency(b.actual)} / ${formatCurrency(b.budgeted)}</div>
            </div>
            <div style="flex: 1;">
                <div class="budget-progress">
                    <div class="progress-bar ${b.status === 'over' ? 'over' : ''}" style="width: ${Math.min(b.percentage, 100)}%"></div>
                </div>
            </div>
            <div class="amount" style="text-align: right;">
                <span class="tag ${b.status === 'over' ? 'expense' : ''}">${b.status === 'over' ? 'Over' : 'Under'}</span>
            </div>
        </div>
    `).join('');
}

// Display Category Breakdown
function displayCategoryBreakdown(data) {
    const container = document.getElementById('categoryBreakdown');
    if (!data.categories || data.categories.length === 0) {
        container.innerHTML = '<p>No expenses to display</p>';
        return;
    }

    container.innerHTML = data.categories.map(c => `
        <div class="category-row">
            <div class="name">${c.category}</div>
            <div>
                <span class="amount">${formatCurrency(c.amount)}</span>
                <span class="percent">(${c.percentage}%)</span>
            </div>
        </div>
    `).join('');
}

// ==========================================
// Charts & Summaries Functions
// ==========================================

// Charts & Summaries state
const csState = {
    expenseChart: null,
    incomeChart: null,
    data: null
};

// Initialize Charts & Summaries page
function initChartsSummaries() {
    // Populate Bahá'í month selector
    const badiMonthSelect = document.getElementById('csBadiMonth');
    if (badiMonthSelect && badiMonthSelect.options.length === 0) {
        BADI_MONTHS.forEach(month => {
            const option = document.createElement('option');
            option.value = month.number;
            option.textContent = `${month.name} (${month.meaning})`;
            badiMonthSelect.appendChild(option);
        });
    }
    
    // Set default values
    const today = new Date();
    const gregorianMonth = document.getElementById('csGregorianMonth');
    if (gregorianMonth) {
        gregorianMonth.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
    }
    
    const badiYear = document.getElementById('csBadiYear');
    if (badiYear) {
        badiYear.value = state.badiYear || (today.getFullYear() - 1844 + 1);
    }
    
    // Set Gregorian year default
    const gregorianYear = document.getElementById('csGregorianYear');
    if (gregorianYear) {
        gregorianYear.value = today.getFullYear();
    }
    
    // Set Bahá'í year only default
    const badiYearOnly = document.getElementById('csBadiYearOnly');
    if (badiYearOnly) {
        badiYearOnly.value = state.badiYear || (today.getFullYear() - 1844 + 1);
    }
    
    const customStart = document.getElementById('csCustomStart');
    const customEnd = document.getElementById('csCustomEnd');
    if (customStart && customEnd) {
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        customStart.value = firstDay.toISOString().split('T')[0];
        customEnd.value = today.toISOString().split('T')[0];
    }
    
    // Setup event listeners
    setupChartsSummariesListeners();
    
    // Initialize comparison controls
    initComparisonControls();
}

// Setup event listeners for Charts & Summaries
function setupChartsSummariesListeners() {
    // Time frame type change
    const timeFrameType = document.getElementById('csTimeFrameType');
    if (timeFrameType) {
        timeFrameType.addEventListener('change', (e) => {
            const value = e.target.value;
            document.getElementById('csGregorianSelector').style.display = value === 'gregorian-month' ? 'flex' : 'none';
            document.getElementById('csGregorianYearSelector').style.display = value === 'gregorian-year' ? 'flex' : 'none';
            document.getElementById('csBadiSelector').style.display = value === 'badi-month' ? 'flex' : 'none';
            document.getElementById('csBadiYearSelector').style.display = value === 'badi-year' ? 'flex' : 'none';
            document.getElementById('csCustomSelector').style.display = value === 'custom' ? 'flex' : 'none';
        });
    }
    
    // Generate button
    const generateBtn = document.getElementById('csGenerateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateChartsSummaries);
    }
    
    // Print button dropdown
    const printBtn = document.getElementById('csPrintBtn');
    const printMenu = document.getElementById('csPrintMenu');
    
    if (printBtn && printMenu) {
        // Toggle menu on button click
        printBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            printMenu.classList.toggle('show');
        });
        
        // Handle orientation option clicks
        document.querySelectorAll('.cs-print-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const orientation = e.currentTarget.dataset.orientation;
                printMenu.classList.remove('show');
                printChartsSummaries(orientation);
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.cs-print-dropdown')) {
                printMenu.classList.remove('show');
            }
        });
    }
}

// Load Charts & Summaries page
async function loadChartsSummaries() {
    initChartsSummaries();
    await generateChartsSummaries();
}

// Get date range based on selected time frame
function getCSDateRange() {
    const timeFrameType = document.getElementById('csTimeFrameType').value;
    let startDate, endDate, label;
    
    if (timeFrameType === 'gregorian-month') {
        const monthValue = document.getElementById('csGregorianMonth').value;
        if (!monthValue) return null;
        
        const [year, month] = monthValue.split('-').map(Number);
        startDate = new Date(year, month - 1, 1);
        endDate = new Date(year, month, 0); // Last day of month
        
        label = startDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    } else if (timeFrameType === 'gregorian-year') {
        const year = parseInt(document.getElementById('csGregorianYear').value);
        if (!year) return null;
        
        startDate = new Date(year, 0, 1); // January 1
        endDate = new Date(year, 11, 31); // December 31
        
        label = `Year ${year}`;
    } else if (timeFrameType === 'badi-month') {
        const badiYear = parseInt(document.getElementById('csBadiYear').value);
        const badiMonth = parseInt(document.getElementById('csBadiMonth').value);
        
        if (!badiYear || isNaN(badiMonth)) return null;
        
        // Convert Bahá'í dates to Gregorian
        const range = getBadiMonthDateRange(badiYear, badiMonth);
        startDate = range.start;
        endDate = range.end;
        
        const monthInfo = BADI_MONTHS.find(m => m.number === badiMonth);
        label = `${monthInfo ? monthInfo.name : 'Month ' + badiMonth} ${badiYear} BE`;
    } else if (timeFrameType === 'badi-year') {
        const badiYear = parseInt(document.getElementById('csBadiYearOnly').value);
        if (!badiYear) return null;
        
        // Bahá'í year starts at Naw-Rúz (March 20/21) and ends the day before next Naw-Rúz
        const range = getBadiYearDateRange(badiYear);
        startDate = range.start;
        endDate = range.end;
        
        label = `Bahá'í Year ${badiYear} BE`;
    } else {
        // Custom range
        const start = document.getElementById('csCustomStart').value;
        const end = document.getElementById('csCustomEnd').value;
        
        if (!start || !end) return null;
        
        startDate = new Date(start);
        endDate = new Date(end);
        
        label = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
    }
    
    return {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0],
        label
    };
}

// Generate Charts & Summaries
async function generateChartsSummaries() {
    const dateRange = getCSDateRange();
    if (!dateRange) {
        alert('Please select a valid date range');
        return;
    }
    
    // Show loading state
    const generateBtn = document.getElementById('csGenerateBtn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    }
    
    try {
        // Fetch transactions for the date range
        const params = new URLSearchParams({
            start_date: dateRange.start,
            end_date: dateRange.end,
            include_excluded: 'false'
        });
        
        const response = await apiFetch(`${API_URL}/transactions/?${params}`);
        if (!response.ok) throw new Error('Failed to load transactions');
        
        const data = await response.json();
        
        // API returns array directly, not {transactions: [...]}
        const transactions = Array.isArray(data) ? data : (data.transactions || []);
        csState.data = { transactions, dateRange };
        
        // Calculate summaries
        let totalIncome = 0;
        let totalExpenses = 0;
        const expensesByCategory = {};
        const incomeByCategory = {};
        
        transactions.forEach(t => {
            const cat = t.category_name || t.category || 'Uncategorized';
            if (t.type === 'income') {
                totalIncome += t.amount;
                incomeByCategory[cat] = (incomeByCategory[cat] || 0) + t.amount;
            } else {
                totalExpenses += t.amount;
                expensesByCategory[cat] = (expensesByCategory[cat] || 0) + t.amount;
            }
        });
        
        // Update summary cards
        document.getElementById('csTotalIncome').textContent = formatCurrency(totalIncome);
        document.getElementById('csTotalExpenses').textContent = formatCurrency(totalExpenses);
        document.getElementById('csNetBalance').textContent = formatCurrency(totalIncome - totalExpenses);
        document.getElementById('csTransactionCount').textContent = transactions.length;
        
        // Update net balance color
        const netBalanceEl = document.getElementById('csNetBalance');
        if (totalIncome - totalExpenses >= 0) {
            netBalanceEl.style.color = '#27ae60';
        } else {
            netBalanceEl.style.color = '#e74c3c';
        }
        
        // Prepare chart data
        const chartType = document.getElementById('csChartType').value;
        const chartColors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
            '#8e44ad', '#27ae60', '#d35400', '#2980b9', '#f1c40f'
        ];
        
        // Update expense chart
        updateCSChart('csExpenseChart', 'expense', expensesByCategory, chartType, chartColors);
        
        // Update income chart
        updateCSChart('csIncomeChart', 'income', incomeByCategory, chartType, chartColors);
        
        // Update tables
        updateCSTables(expensesByCategory, incomeByCategory, transactions);
        
        // Update top transactions
        updateCSTopTransactions(transactions);
        
        // Update print header
        document.getElementById('csPrintDateRange').textContent = `Period: ${dateRange.label}`;
        document.getElementById('csPrintGeneratedDate').textContent = `Generated: ${new Date().toLocaleString()}`;
        
        // Show preview message
        if (transactions.length === 0) {
            alert(`No transactions found for ${dateRange.label}.\n\nTry selecting a different date range.`);
        } else {
            // Show success notification with summary
            const summaryMsg = `Report generated for ${dateRange.label}\n\n` +
                `📊 Transactions: ${transactions.length}\n` +
                `💰 Income: ${formatCurrency(totalIncome)}\n` +
                `💸 Expenses: ${formatCurrency(totalExpenses)}\n` +
                `📈 Net: ${formatCurrency(totalIncome - totalExpenses)}\n\n` +
                `Click "Print Portrait" or "Print Landscape" to print this report.`;
            
            // Show brief notification
            showCSNotification(`Report ready: ${transactions.length} transactions for ${dateRange.label}`);
        }
        
        // Clear the form
        document.getElementById('csCustomStart').value = '';
        document.getElementById('csCustomEnd').value = '';
        
    } catch (error) {
        console.error('Error generating charts & summaries:', error);
        alert('Error generating report: ' + error.message);
    } finally {
        // Reset button state
        const generateBtn = document.getElementById('csGenerateBtn');
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-sync"></i> Generate';
        }
    }
}

// Show notification for Charts & Summaries
function showCSNotification(message) {
    // Create or get notification element
    let notification = document.getElementById('csNotification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'csNotification';
        notification.className = 'cs-notification';
        document.querySelector('.charts-summaries-container')?.prepend(notification);
    }
    
    notification.textContent = message;
    notification.style.display = 'block';
    notification.classList.add('show');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.style.display = 'none';
        }, 300);
    }, 5000);
}

// Update a chart
function updateCSChart(canvasId, type, dataObj, chartType, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    
    // Destroy existing chart
    if (type === 'expense' && csState.expenseChart) {
        csState.expenseChart.destroy();
    } else if (type === 'income' && csState.incomeChart) {
        csState.incomeChart.destroy();
    }
    
    const labels = Object.keys(dataObj);
    const data = Object.values(dataObj);
    
    if (labels.length === 0) {
        ctx.parentElement.querySelector('canvas').style.display = 'none';
        return;
    }
    
    ctx.style.display = 'block';
    
    const chartConfig = {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: type === 'expense' ? 'Expenses' : 'Income',
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: chartType === 'line' ? colors[0] : colors.slice(0, labels.length),
                borderWidth: chartType === 'line' ? 2 : 1,
                fill: chartType === 'line',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: ['pie', 'doughnut', 'polarArea'].includes(chartType),
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                            return `${context.label}: ${formatCurrency(value)}`;
                        }
                    }
                }
            },
            scales: ['pie', 'doughnut', 'polarArea', 'radar'].includes(chartType) ? {} : {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    };
    
    const chart = new Chart(ctx, chartConfig);
    
    if (type === 'expense') {
        csState.expenseChart = chart;
    } else {
        csState.incomeChart = chart;
    }
}

// Update tables
function updateCSTables(expensesByCategory, incomeByCategory, transactions) {
    // Expense table
    const expenseTotal = Object.values(expensesByCategory).reduce((a, b) => a + b, 0);
    const expenseBody = document.getElementById('csExpenseTableBody');
    const expenseTransactions = transactions.filter(t => t.type === 'expense');
    
    if (Object.keys(expensesByCategory).length === 0) {
        expenseBody.innerHTML = '<tr><td colspan="4">No expense data</td></tr>';
    } else {
        expenseBody.innerHTML = Object.entries(expensesByCategory)
            .sort((a, b) => b[1] - a[1])
            .map(([category, amount]) => {
                const count = expenseTransactions.filter(t => (t.category_name || t.category || 'Uncategorized') === category).length;
                const percentage = expenseTotal > 0 ? ((amount / expenseTotal) * 100).toFixed(1) : 0;
                return `
                    <tr>
                        <td>${category}</td>
                        <td>${formatCurrency(amount)}</td>
                        <td>${percentage}%</td>
                        <td>${count}</td>
                    </tr>
                `;
            }).join('');
    }
    
    document.getElementById('csExpenseTableTotal').textContent = formatCurrency(expenseTotal);
    document.getElementById('csExpenseTableCount').textContent = expenseTransactions.length;
    
    // Income table
    const incomeTotal = Object.values(incomeByCategory).reduce((a, b) => a + b, 0);
    const incomeBody = document.getElementById('csIncomeTableBody');
    const incomeTransactions = transactions.filter(t => t.type === 'income');
    
    if (Object.keys(incomeByCategory).length === 0) {
        incomeBody.innerHTML = '<tr><td colspan="4">No income data</td></tr>';
    } else {
        incomeBody.innerHTML = Object.entries(incomeByCategory)
            .sort((a, b) => b[1] - a[1])
            .map(([category, amount]) => {
                const count = incomeTransactions.filter(t => (t.category_name || t.category || 'Uncategorized') === category).length;
                const percentage = incomeTotal > 0 ? ((amount / incomeTotal) * 100).toFixed(1) : 0;
                return `
                    <tr>
                        <td>${category}</td>
                        <td>${formatCurrency(amount)}</td>
                        <td>${percentage}%</td>
                        <td>${count}</td>
                    </tr>
                `;
            }).join('');
    }
    
    document.getElementById('csIncomeTableTotal').textContent = formatCurrency(incomeTotal);
    document.getElementById('csIncomeTableCount').textContent = incomeTransactions.length;
}

// Update top transactions
function updateCSTopTransactions(transactions) {
    const tbody = document.getElementById('csTopTransactionsBody');
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No transactions found</td></tr>';
        return;
    }
    
    // Sort by amount (descending) and take top 10
    const topTransactions = [...transactions]
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 10);
    
    tbody.innerHTML = topTransactions.map(t => `
        <tr>
            <td>${new Date(t.date).toLocaleDateString()}</td>
            <td>${escapeHtml(t.description)}</td>
            <td>${t.category_name || t.category || 'Uncategorized'}</td>
            <td><span class="tag ${t.type}">${t.type}</span></td>
            <td>${formatCurrency(t.amount)}</td>
        </tr>
    `).join('');
}

// Print Charts & Summaries
function printChartsSummaries(orientation) {
    // Create a style element for page orientation
    const styleId = 'print-orientation-style';
    let styleEl = document.getElementById(styleId);
    
    if (!styleEl) {
        styleEl = document.createElement('style');
        styleEl.id = styleId;
        document.head.appendChild(styleEl);
    }
    
    // Set the page orientation
    if (orientation === 'landscape') {
        styleEl.textContent = '@page { size: landscape; margin: 1cm; }';
    } else {
        styleEl.textContent = '@page { size: portrait; margin: 1cm; }';
    }
    
    // Trigger print
    window.print();
}

// Print Comparison function
function printComparison(orientation) {
    // Hide the print options dropdown
    const printOptions = document.getElementById('csComparePrintOptions');
    if (printOptions) {
        printOptions.classList.remove('show');
    }
    
    // Reuse the same print logic
    printChartsSummaries(orientation);
}

// ==========================================
// Period Comparison Functions
// ==========================================

const compareState = {
    expenseChart: null,
    incomeChart: null,
    expenseOverlay: null,
    incomeOverlay: null
};

// Initialize comparison controls
function initComparisonControls() {
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    
    // Set default values for Period 1 (current month)
    const compare1Month = document.getElementById('csCompare1Month');
    if (compare1Month) {
        compare1Month.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
    }
    
    // Set default values for Period 2 (last month)
    const compare2Month = document.getElementById('csCompare2Month');
    if (compare2Month) {
        compare2Month.value = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;
    }
    
    // Setup period type change listeners
    setupPeriodTypeListener('csCompare1Type', 'csCompare1Inputs', 1);
    setupPeriodTypeListener('csCompare2Type', 'csCompare2Inputs', 2);
    
    // Compare button
    const compareBtn = document.getElementById('csCompareBtn');
    if (compareBtn) {
        compareBtn.addEventListener('click', runComparison);
    }
    
    // View mode toggle
    const viewMode = document.getElementById('csCompareViewMode');
    if (viewMode) {
        viewMode.addEventListener('change', (e) => {
            const sideBySide = document.getElementById('csCompareSideBySide');
            const overlay = document.getElementById('csCompareOverlay');
            
            if (e.target.value === 'side-by-side') {
                sideBySide.style.display = 'grid';
                overlay.style.display = 'none';
            } else {
                sideBySide.style.display = 'none';
                overlay.style.display = 'grid';
            }
        });
    }
    
    // Print button toggle
    const printBtn = document.getElementById('csComparePrintBtn');
    const printOptions = document.getElementById('csComparePrintOptions');
    if (printBtn && printOptions) {
        printBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            printOptions.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!printBtn.contains(e.target) && !printOptions.contains(e.target)) {
                printOptions.classList.remove('show');
            }
        });
    }
}

// Setup period type change listener
function setupPeriodTypeListener(selectId, inputsId, periodNum) {
    const select = document.getElementById(selectId);
    const inputsDiv = document.getElementById(inputsId);
    
    if (!select || !inputsDiv) return;
    
    select.addEventListener('change', (e) => {
        const type = e.target.value;
        let html = '';
        
        const today = new Date();
        const badiYear = today.getFullYear() - 1844 + 1;
        
        switch (type) {
            case 'gregorian-month':
                html = `<input type="month" id="csCompare${periodNum}Month" class="form-control" value="${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}">`;
                break;
            case 'gregorian-year':
                html = `<input type="number" id="csCompare${periodNum}Year" class="form-control" value="${today.getFullYear()}" min="1900" max="2100" style="width: 100px;">`;
                break;
            case 'badi-month':
                html = `
                    <input type="number" id="csCompare${periodNum}BadiYear" class="form-control" value="${badiYear}" min="1" style="width: 80px;">
                    <select id="csCompare${periodNum}BadiMonth" class="form-control">
                        ${BADI_MONTHS.map(m => `<option value="${m.number}">${m.name}</option>`).join('')}
                    </select>
                `;
                break;
            case 'badi-year':
                html = `<input type="number" id="csCompare${periodNum}BadiYearOnly" class="form-control" value="${badiYear}" min="1" style="width: 100px;">`;
                break;
            case 'custom':
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                html = `
                    <input type="date" id="csCompare${periodNum}Start" class="form-control" value="${firstDay.toISOString().split('T')[0]}">
                    <span>to</span>
                    <input type="date" id="csCompare${periodNum}End" class="form-control" value="${today.toISOString().split('T')[0]}">
                `;
                break;
        }
        
        inputsDiv.innerHTML = html;
    });
}

// Get date range for a comparison period
function getComparePeriodRange(periodNum) {
    const type = document.getElementById(`csCompare${periodNum}Type`).value;
    let startDate, endDate, label;
    
    switch (type) {
        case 'gregorian-month': {
            const monthValue = document.getElementById(`csCompare${periodNum}Month`)?.value;
            if (!monthValue) return null;
            const [year, month] = monthValue.split('-').map(Number);
            startDate = new Date(year, month - 1, 1);
            endDate = new Date(year, month, 0); // Last day of month
            label = startDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
            break;
        }
        case 'gregorian-year': {
            const year = parseInt(document.getElementById(`csCompare${periodNum}Year`)?.value);
            if (!year) return null;
            startDate = new Date(year, 0, 1); // January 1
            endDate = new Date(year, 11, 31); // December 31
            label = `Year ${year}`;
            break;
        }
        case 'badi-month': {
            const badiYear = parseInt(document.getElementById(`csCompare${periodNum}BadiYear`)?.value);
            const badiMonth = parseInt(document.getElementById(`csCompare${periodNum}BadiMonth`)?.value);
            if (!badiYear || isNaN(badiMonth)) return null;
            const range = getBadiMonthDateRange(badiYear, badiMonth);
            startDate = range.start;
            endDate = range.end;
            const monthInfo = BADI_MONTHS.find(m => m.number === badiMonth);
            label = `${monthInfo ? monthInfo.name : 'Month ' + badiMonth} ${badiYear} BE`;
            break;
        }
        case 'badi-year': {
            const badiYear = parseInt(document.getElementById(`csCompare${periodNum}BadiYearOnly`)?.value);
            if (!badiYear) return null;
            const range = getBadiYearDateRange(badiYear);
            startDate = range.start;
            endDate = range.end;
            label = `Bahá'í Year ${badiYear} BE`;
            break;
        }
        case 'custom': {
            const start = document.getElementById(`csCompare${periodNum}Start`)?.value;
            const end = document.getElementById(`csCompare${periodNum}End`)?.value;
            if (!start || !end) return null;
            startDate = new Date(start);
            endDate = new Date(end);
            label = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;
            break;
        }
    }
    
    return {
        start: startDate.toISOString().split('T')[0],
        end: endDate.toISOString().split('T')[0],
        label
    };
}

// Fetch transactions for a period
async function fetchPeriodData(range) {
    const params = new URLSearchParams({
        start_date: range.start,
        end_date: range.end,
        include_excluded: 'false'
    });
    
    const response = await apiFetch(`${API_URL}/transactions/?${params}`);
    if (!response.ok) throw new Error('Failed to load transactions');
    
    const data = await response.json();
    const transactions = Array.isArray(data) ? data : (data.transactions || []);
    
    // Calculate summaries
    let totalIncome = 0;
    let totalExpenses = 0;
    const expensesByCategory = {};
    const incomeByCategory = {};
    
    transactions.forEach(t => {
        const cat = t.category_name || t.category || 'Uncategorized';
        if (t.type === 'income') {
            totalIncome += t.amount;
            incomeByCategory[cat] = (incomeByCategory[cat] || 0) + t.amount;
        } else {
            totalExpenses += t.amount;
            expensesByCategory[cat] = (expensesByCategory[cat] || 0) + t.amount;
        }
    });
    
    return {
        totalIncome,
        totalExpenses,
        expensesByCategory,
        incomeByCategory,
        transactions
    };
}

// Run comparison
async function runComparison() {
    const range1 = getComparePeriodRange(1);
    const range2 = getComparePeriodRange(2);
    
    if (!range1 || !range2) {
        alert('Please select valid date ranges for both periods');
        return;
    }
    
    const compareBtn = document.getElementById('csCompareBtn');
    compareBtn.disabled = true;
    compareBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Comparing...';
    
    try {
        const [data1, data2] = await Promise.all([
            fetchPeriodData(range1),
            fetchPeriodData(range2)
        ]);
        
        // Update labels
        document.getElementById('csCompare1Label').textContent = range1.label;
        document.getElementById('csCompare2Label').textContent = range2.label;
        
        // Update summary cards
        document.getElementById('csCompare1Income').textContent = formatCurrency(data1.totalIncome);
        document.getElementById('csCompare1Expenses').textContent = formatCurrency(data1.totalExpenses);
        document.getElementById('csCompare1Net').textContent = formatCurrency(data1.totalIncome - data1.totalExpenses);
        
        document.getElementById('csCompare2Income').textContent = formatCurrency(data2.totalIncome);
        document.getElementById('csCompare2Expenses').textContent = formatCurrency(data2.totalExpenses);
        document.getElementById('csCompare2Net').textContent = formatCurrency(data2.totalIncome - data2.totalExpenses);
        
        // Calculate differences
        const diffIncome = data2.totalIncome - data1.totalIncome;
        const diffExpenses = data2.totalExpenses - data1.totalExpenses;
        const diffNet = (data2.totalIncome - data2.totalExpenses) - (data1.totalIncome - data1.totalExpenses);
        
        document.getElementById('csCompareDiffIncome').textContent = (diffIncome >= 0 ? '+' : '') + formatCurrency(diffIncome);
        document.getElementById('csCompareDiffExpenses').textContent = (diffExpenses >= 0 ? '+' : '') + formatCurrency(diffExpenses);
        document.getElementById('csCompareDiffNet').textContent = (diffNet >= 0 ? '+' : '') + formatCurrency(diffNet);
        
        // Color the differences
        document.getElementById('csCompareDiffIncome').style.color = diffIncome >= 0 ? '#27ae60' : '#e74c3c';
        document.getElementById('csCompareDiffExpenses').style.color = diffExpenses <= 0 ? '#27ae60' : '#e74c3c';
        document.getElementById('csCompareDiffNet').style.color = diffNet >= 0 ? '#27ae60' : '#e74c3c';
        
        // Generate charts
        generateComparisonCharts(data1, data2, range1.label, range2.label);
        
        // Show results
        document.getElementById('csComparisonResults').style.display = 'block';
        
    } catch (error) {
        console.error('Error running comparison:', error);
        alert('Error comparing periods: ' + error.message);
    } finally {
        compareBtn.disabled = false;
        compareBtn.innerHTML = '<i class="fas fa-chart-bar"></i> Compare';
    }
}

// Generate comparison charts
function generateComparisonCharts(data1, data2, label1, label2) {
    const chartType = document.getElementById('csCompareChartType')?.value || 'bar';
    const viewMode = document.getElementById('csCompareViewMode')?.value || 'side-by-side';
    
    const colors1 = 'rgba(52, 152, 219, 0.7)';  // Blue with transparency
    const colors2 = 'rgba(231, 76, 60, 0.7)';   // Red with transparency
    const border1 = '#3498db';
    const border2 = '#e74c3c';
    
    // Generate color palette for pie/doughnut/polar charts
    const generateColors = (count) => {
        const baseColors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
            '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
            '#27ae60', '#8e44ad', '#2980b9', '#d35400', '#7f8c8d'
        ];
        return baseColors.slice(0, count);
    };
    
    // Get all unique categories
    const allExpenseCategories = [...new Set([
        ...Object.keys(data1.expensesByCategory),
        ...Object.keys(data2.expensesByCategory)
    ])].sort();
    
    const allIncomeCategories = [...new Set([
        ...Object.keys(data1.incomeByCategory),
        ...Object.keys(data2.incomeByCategory)
    ])].sort();
    
    // Determine if chart type supports multiple datasets or needs separate charts
    const isMultiDatasetType = ['bar', 'line', 'radar'].includes(chartType);
    const isPieType = ['pie', 'doughnut', 'polarArea'].includes(chartType);
    
    // Build chart configuration based on type
    const buildChartConfig = (type, labels, data1Arr, data2Arr, lab1, lab2, isOverlay) => {
        const expenseColors = generateColors(labels.length);
        
        if (isPieType) {
            // For pie/doughnut/polar, we need separate charts for each period
            // In side-by-side, show period 1 data; overlay will show period 2
            const dataArr = isOverlay ? data2Arr : data1Arr;
            const label = isOverlay ? lab2 : lab1;
            return {
                type: type,
                data: {
                    labels: labels,
                    datasets: [{
                        label: label,
                        data: dataArr,
                        backgroundColor: expenseColors.map(c => c + 'cc'),
                        borderColor: expenseColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { 
                        legend: { display: true, position: 'right' },
                        title: { display: true, text: label }
                    }
                }
            };
        } else {
            // Bar, line, radar - support multiple datasets
            const config = {
                type: type,
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: lab1,
                            data: data1Arr,
                            backgroundColor: isOverlay ? 'rgba(52, 152, 219, 0.5)' : colors1,
                            borderColor: border1,
                            borderWidth: type === 'line' ? 2 : 1,
                            fill: type === 'line' || type === 'radar',
                            tension: 0.4,
                            // For overlay bar charts, both bars same size/position
                            barPercentage: isOverlay && type === 'bar' ? 1.0 : 0.9,
                            categoryPercentage: isOverlay && type === 'bar' ? 0.7 : 0.8,
                            order: isOverlay && type === 'bar' ? 2 : 1  // Draw first (behind)
                        },
                        {
                            label: lab2,
                            data: data2Arr,
                            backgroundColor: isOverlay ? 'rgba(231, 76, 60, 0.5)' : colors2,
                            borderColor: border2,
                            borderWidth: type === 'line' ? 2 : 1,
                            fill: type === 'line' || type === 'radar',
                            tension: 0.4,
                            // For overlay bar charts, both bars same size/position
                            barPercentage: isOverlay && type === 'bar' ? 1.0 : 0.9,
                            categoryPercentage: isOverlay && type === 'bar' ? 0.7 : 0.8,
                            order: isOverlay && type === 'bar' ? 1 : 2  // Draw second (in front)
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: true, position: 'top' } },
                    scales: type === 'radar' ? {} : { y: { beginAtZero: true } }
                }
            };
            return config;
        }
    };
    
    // Side by side expense chart
    if (compareState.expenseChart) compareState.expenseChart.destroy();
    const expenseCtx = document.getElementById('csCompareExpenseChart');
    if (expenseCtx && allExpenseCategories.length > 0) {
        const expData1 = allExpenseCategories.map(cat => data1.expensesByCategory[cat] || 0);
        const expData2 = allExpenseCategories.map(cat => data2.expensesByCategory[cat] || 0);
        compareState.expenseChart = new Chart(expenseCtx, 
            buildChartConfig(chartType, allExpenseCategories, expData1, expData2, label1, label2, false)
        );
    }
    
    // Side by side income chart
    if (compareState.incomeChart) compareState.incomeChart.destroy();
    const incomeCtx = document.getElementById('csCompareIncomeChart');
    if (incomeCtx && allIncomeCategories.length > 0) {
        const incData1 = allIncomeCategories.map(cat => data1.incomeByCategory[cat] || 0);
        const incData2 = allIncomeCategories.map(cat => data2.incomeByCategory[cat] || 0);
        compareState.incomeChart = new Chart(incomeCtx,
            buildChartConfig(chartType, allIncomeCategories, incData1, incData2, label1, label2, false)
        );
    }
    
    // Overlay expense chart
    if (compareState.expenseOverlay) compareState.expenseOverlay.destroy();
    const expenseOverlayCtx = document.getElementById('csCompareExpenseOverlay');
    if (expenseOverlayCtx && allExpenseCategories.length > 0) {
        const expData1 = allExpenseCategories.map(cat => data1.expensesByCategory[cat] || 0);
        const expData2 = allExpenseCategories.map(cat => data2.expensesByCategory[cat] || 0);
        compareState.expenseOverlay = new Chart(expenseOverlayCtx,
            buildChartConfig(chartType, allExpenseCategories, expData1, expData2, label1, label2, true)
        );
    }
    
    // Overlay income chart
    if (compareState.incomeOverlay) compareState.incomeOverlay.destroy();
    const incomeOverlayCtx = document.getElementById('csCompareIncomeOverlay');
    if (incomeOverlayCtx && allIncomeCategories.length > 0) {
        const incData1 = allIncomeCategories.map(cat => data1.incomeByCategory[cat] || 0);
        const incData2 = allIncomeCategories.map(cat => data2.incomeByCategory[cat] || 0);
        compareState.incomeOverlay = new Chart(incomeOverlayCtx,
            buildChartConfig(chartType, allIncomeCategories, incData1, incData2, label1, label2, true)
        );
    }
}

// File Upload Handling
let selectedFile = null;

async function handleFileSelect(files) {
    if (!files || files.length === 0) return;

    selectedFile = files[0];
    
    const allowedTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                          'application/vnd.ms-excel'];
    
    if (!allowedTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.csv') && 
        !selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
        alert('Please select a valid file (CSV, XLSX, or XLS)');
        return;
    }

    // Preview file
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await apiFetch(`${API_URL}/uploads/preview`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Failed to preview file');

        const result = await response.json();
        displayPreview(result.preview);
        document.getElementById('uploadPreview').style.display = 'block';
    } catch (error) {
        console.error('Error previewing file:', error);
        alert('Error previewing file: ' + error.message);
    }
}

function displayPreview(data) {
    const tbody = document.getElementById('previewBody');
    tbody.innerHTML = data.map(row => `
        <tr>
            <td>${row.date}</td>
            <td>${row.description}</td>
            <td>${formatCurrency(row.amount)}</td>
            <td><span class="tag ${row.type}">${row.type}</span></td>
            <td>${row.category}</td>
        </tr>
    `).join('');
}

async function confirmUpload() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    
    // Add uploaded_by from current user
    if (state.currentUser) {
        formData.append('uploaded_by', state.currentUser.username);
    }

    try {
        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.className = 'upload-status loading';
        statusDiv.textContent = 'Uploading and processing...';
        statusDiv.style.display = 'block';

        const response = await apiFetch(`${API_URL}/uploads/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Upload failed');
        }
        
        statusDiv.className = 'upload-status success';
        statusDiv.innerHTML = `
            <strong>Success!</strong><br>
            ${result.transactions_created} transactions imported successfully.
        `;

        document.getElementById('uploadPreview').style.display = 'none';
        document.getElementById('fileInput').value = '';
        selectedFile = null;

        // Refresh upload history
        loadUploadHistory();

        setTimeout(() => {
            navigateTo('transactions');
            loadTransactions();
        }, 2000);
    } catch (error) {
        console.error('Error uploading file:', error);
        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.className = 'upload-status error';
        statusDiv.textContent = 'Error uploading file: ' + error.message;
    }
}

// Utility to reset upload state/UI
function resetUploadUI() {
    selectedFile = null;
    document.getElementById('uploadPreview').style.display = 'none';
    document.getElementById('fileInput').value = '';
    const statusDiv = document.getElementById('uploadStatus');
    if (statusDiv) {
        statusDiv.style.display = 'none';
        statusDiv.className = 'upload-status';
        statusDiv.textContent = '';
    }
    const tbody = document.getElementById('previewBody');
    if (tbody) tbody.innerHTML = '';
}

// Replace cancelUploadBtn handler to use resetUploadUI
const cancelBtn = document.getElementById('cancelUploadBtn');
if (cancelBtn) {
    cancelBtn.addEventListener('click', resetUploadUI);
}

// ==========================================
// Rules
// ==========================================

// Load Rules
async function loadRules() {
    if (state.currentPage !== 'rules') return;

    const isSuperuser = state.currentUser && state.currentUser.role === 'superuser';

    // Show/hide admin-only controls in the rules page header and table
    document.querySelectorAll('#rules .admin-only').forEach(el => {
        el.style.display = isSuperuser ? '' : 'none';
    });
    // Show/hide the scope selector inside the rule modal
    const scopeGroup = document.getElementById('ruleScopeGroup');
    if (scopeGroup) scopeGroup.style.display = isSuperuser ? '' : 'none';
    
    try {
        const response = await apiFetch(`${API_URL}/rules/`);
        if (!response.ok) throw new Error('Failed to load rules');
        
        const rules = await response.json();
        displayRules(rules);
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

// Display Rules
function displayRules(rules) {
    const isSuperuser = state.currentUser && state.currentUser.role === 'superuser';
    const tbody = document.getElementById('rulesBody');
    tbody.innerHTML = rules.map(r => `
        <tr>
            <td><strong>${r.name}</strong></td>
            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">${r.keywords}</td>
            <td>${r.category_name}</td>
            <td>${r.priority}</td>
            <td>
                <span class="rule-status ${r.is_active ? 'active' : 'inactive'}">
                    ${r.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td style="${isSuperuser ? '' : 'display:none'}">
                <span class="rule-scope-badge ${r.scope === 'all' ? 'scope-all' : 'scope-self'}">
                    ${r.scope === 'all'
                        ? '<i class="fas fa-globe"></i> All Users'
                        : '<i class="fas fa-user"></i> Personal'}
                </span>
            </td>
            <td>
                <div class="actions">
                    <button class="btn-icon edit" title="Edit" onclick="editRule(${r.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon delete" title="Delete" onclick="deleteRule(${r.id})" style="${isSuperuser ? '' : 'display:none'}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Edit Rule
async function editRule(id) {
    try {
        const response = await apiFetch(`${API_URL}/rules/${id}`);
        if (!response.ok) {
            let msg = 'Failed to load rule';
            try { const e = await response.json(); msg = e.error || msg; } catch (_) {}
            throw new Error(msg);
        }
        
        const rule = await response.json();
        
        // Populate form
        document.getElementById('ruleName').value = rule.name;
        document.getElementById('ruleKeywords').value = rule.keywords;
        document.getElementById('ruleCategory').value = rule.category_id;
        document.getElementById('rulePriority').value = rule.priority;
        document.getElementById('ruleActive').checked = rule.is_active;

        // Populate scope radio
        const scopeRadio = document.querySelector(`input[name="ruleScope"][value="${rule.scope || 'all'}"]`);
        if (scopeRadio) scopeRadio.checked = true;
        
        // Update form to edit mode
        document.getElementById('ruleModalTitle').textContent = 'Edit Categorization Rule';
        document.getElementById('ruleForm').dataset.ruleId = id;
        
        openModal('ruleModal');
    } catch (error) {
        console.error('Error loading rule:', error);
        alert(error.message || 'Failed to load rule');
    }
}

// Delete Rule
async function deleteRule(id) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
        const response = await apiFetch(`${API_URL}/rules/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            let msg = 'Failed to delete rule';
            try { const e = await response.json(); msg = e.error || msg; } catch (_) {}
            throw new Error(msg);
        }
        
        loadRules();
    } catch (error) {
        console.error('Error deleting rule:', error);
        alert(error.message || 'Failed to delete rule');
    }
}

// Handle Rule Submit
async function handleRuleSubmit(e) {
    e.preventDefault();
    
    const name = document.getElementById('ruleName').value.trim();
    const keywords = document.getElementById('ruleKeywords').value.trim();
    const category_id = parseInt(document.getElementById('ruleCategory').value);
    const priority = parseInt(document.getElementById('rulePriority').value);
    const is_active = document.getElementById('ruleActive').checked;
    const ruleId = document.getElementById('ruleForm').dataset.ruleId;
    const scopeEl = document.querySelector('input[name="ruleScope"]:checked');
    const scope = scopeEl ? scopeEl.value : 'all';
    
    if (!name || !keywords || !category_id) {
        alert('Please fill all required fields');
        return;
    }
    
    try {
        const url = ruleId ? 
            `${API_URL}/rules/${ruleId}` :
            `${API_URL}/rules/`;
        
        const method = ruleId ? 'PUT' : 'POST';
        
        const response = await apiFetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                keywords,
                category_id,
                priority,
                is_active,
                scope
            })
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to save rule';
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch (_) {
                errorMessage = `Server error (${response.status})`;
            }
            throw new Error(errorMessage);
        }
        
        closeModal('ruleModal');
        delete document.getElementById('ruleForm').dataset.ruleId;
        document.getElementById('ruleForm').reset();
        document.getElementById('ruleModalTitle').textContent = 'Add Categorization Rule';
        
        loadRules();
    } catch (error) {
        console.error('Error saving rule:', error);
        alert(error.message);
    }
}

// Apply Rules to All Transactions
async function applyRulesToAllTransactions() {
    if (!confirm('This will apply all active categorization rules to existing transactions. Transactions matching rules will have their categories updated. Continue?')) {
        return;
    }
    
    try {
        const response = await apiFetch(`${API_URL}/rules/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to apply rules');
        }
        
        const result = await response.json();
        
        if (result.updated > 0) {
            let message = `Successfully updated ${result.updated} transaction(s).\n\nDetails:\n`;
            result.details.slice(0, 10).forEach(t => {
                message += `• "${t.description.substring(0, 30)}..." → ${t.new_category} (via ${t.rule_name})\n`;
            });
            if (result.details.length > 10) {
                message += `\n... and ${result.details.length - 10} more`;
            }
            alert(message);
        } else {
            alert('No transactions were updated. Either no rules matched or categories are already correct.');
        }
        
        // Refresh transactions if on that page
        if (state.currentPage === 'transactions') {
            loadTransactions();
        }
    } catch (error) {
        console.error('Error applying rules:', error);
        alert(error.message);
    }
}

// Export Rules
async function exportRules() {
    try {
        const response = await apiFetch(`${API_URL}/rules/export`);
        if (!response.ok) throw new Error('Failed to export rules');
        
        const data = await response.json();
        
        if (data.count === 0) {
            alert('No rules to export');
            return;
        }
        
        // Ask user for format
        const format = prompt('Export format: Enter "json", "yaml", or "csv"', 'json');
        if (!format) return;
        
        let content, filename, mimeType;
        const formatLower = format.toLowerCase().trim();
        
        if (formatLower === 'csv') {
            // Convert to CSV
            const headers = ['name', 'keywords', 'category_name', 'category_type', 'priority', 'is_active'];
            const csvRows = [headers.join(',')];
            
            data.rules.forEach(rule => {
                const row = headers.map(header => {
                    let value = rule[header];
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        value = `"${value.replace(/"/g, '""')}"`;
                    }
                    return value ?? '';
                });
                csvRows.push(row.join(','));
            });
            
            content = csvRows.join('\n');
            filename = 'categorization_rules.csv';
            mimeType = 'text/csv';
        } else if (formatLower === 'yaml' || formatLower === 'yml') {
            // Convert to YAML
            const yamlHeader = '# Categorization Rules Export\n# Generated: ' + new Date().toISOString() + '\n\n';
            content = yamlHeader + toYAML(data);
            filename = 'categorization_rules.yaml';
            mimeType = 'text/yaml';
        } else {
            // JSON format (default)
            content = JSON.stringify(data, null, 2);
            filename = 'categorization_rules.json';
            mimeType = 'application/json';
        }
        
        // Download file
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        alert(`Exported ${data.count} rules to ${filename}`);
    } catch (error) {
        console.error('Error exporting rules:', error);
        alert('Error exporting rules: ' + error.message);
    }
}

// Handle Rules Import
async function handleRulesImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    try {
        const text = await file.text();
        let rules;
        const fileName = file.name.toLowerCase();
        
        if (fileName.endsWith('.csv')) {
            // Parse CSV
            const lines = text.split('\n').filter(line => line.trim());
            if (lines.length < 2) {
                throw new Error('CSV file is empty or has no data rows');
            }
            
            const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
            rules = [];
            
            for (let i = 1; i < lines.length; i++) {
                const values = parseCSVLine(lines[i]);
                const rule = {};
                headers.forEach((header, index) => {
                    let value = values[index] || '';
                    if (header === 'priority') {
                        value = parseInt(value) || 0;
                    } else if (header === 'is_active') {
                        value = value.toLowerCase() !== 'false';
                    }
                    rule[header] = value;
                });
                rules.push(rule);
            }
        } else if (fileName.endsWith('.yaml') || fileName.endsWith('.yml')) {
            // Parse YAML
            const data = parseYAML(text);
            rules = data.rules || data;
            
            // Ensure rules is an array
            if (!Array.isArray(rules)) {
                throw new Error('YAML file must contain a "rules" array');
            }
        } else {
            // Parse JSON (default)
            const data = JSON.parse(text);
            rules = data.rules || data;
        }
        
        if (!Array.isArray(rules) || rules.length === 0) {
            throw new Error('No valid rules found in file');
        }
        
        // Confirm import
        if (!confirm(`Found ${rules.length} rules in file. Import them?`)) {
            e.target.value = '';
            return;
        }
        
        const response = await apiFetch(`${API_URL}/rules/import`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ rules })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to import rules');
        }
        
        const result = await response.json();
        
        let message = `Import complete!\n\nImported: ${result.imported}\nSkipped (duplicates): ${result.skipped}\nTotal in file: ${result.total}`;
        if (result.errors && result.errors.length > 0) {
            message += `\n\nErrors:\n${result.errors.slice(0, 5).join('\n')}`;
            if (result.errors.length > 5) {
                message += `\n... and ${result.errors.length - 5} more errors`;
            }
        }
        
        alert(message);
        loadRules();
    } catch (error) {
        console.error('Error importing rules:', error);
        alert('Error importing rules: ' + error.message);
    }
    
    e.target.value = '';
}

// Parse CSV line handling quoted values
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                current += '"';
                i++;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }
    
    values.push(current.trim());
    return values;
}

// Test Rule
async function testRule() {
    const testInput = document.getElementById('ruleTestInput').value.trim();
    if (!testInput) return;
    
    try {
        const response = await apiFetch(`${API_URL}/rules/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                description: testInput
            })
        });
        
        if (!response.ok) throw new Error('Test failed');
        
        const result = await response.json();
        const resultDiv = document.getElementById('ruleTestResult');
        
        if (result.primary_match) {
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #d4edda; border-radius: 4px; color: #155724;">
                    <strong>Match Found!</strong><br>
                    Rule: ${result.primary_match.rule_name}<br>
                    Category: ${result.primary_match.category_name}<br>
                    Priority: ${result.primary_match.priority}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #f8d7da; border-radius: 4px; color: #721c24;">
                    No matching rules found. Would use default category.
                </div>
            `;
        }
        
        resultDiv.style.display = 'block';
    } catch (error) {
        console.error('Error testing rule:', error);
    }
}

// API Status Management
async function loadApiStatus() {
    try {
        const response = await apiFetch(`${API_URL}/status/`);
        if (!response.ok) throw new Error('Failed to load API status');
        
        const status = await response.json();
        updateApiStatusDisplay(status);
        
        // Set up auto-refresh every 5 seconds
        if (window.statusRefreshInterval) {
            clearInterval(window.statusRefreshInterval);
        }
        window.statusRefreshInterval = setInterval(async () => {
            const refreshResponse = await apiFetch(`${API_URL}/status/`);
            if (refreshResponse.ok) {
                const refreshStatus = await refreshResponse.json();
                updateApiStatusDisplay(refreshStatus);
            }
        }, 5000);
    } catch (error) {
        console.error('Error loading API status:', error);
        document.getElementById('statusBadge').textContent = 'Error loading status';
    }
}

function updateApiStatusDisplay(status) {
    const statusBadge = document.getElementById('statusBadge');
    const apiToggle = document.getElementById('apiToggle');
    const statusDetails = document.getElementById('statusDetails');
    
    const isOnline = status.status === 'Online';
    
    // Update badge
    statusBadge.innerHTML = `<span class="status-badge ${isOnline ? 'online' : 'offline'}">${status.status}</span>`;
    
    // Update toggle
    apiToggle.checked = isOnline;
    
    // Update details
    const lastToggled = status.last_toggled 
        ? new Date(status.last_toggled).toLocaleString() 
        : 'Never';
    const toggledBy = status.toggled_by || 'System';
    
    statusDetails.innerHTML = `
        <div class="detail-row">
            <label>Status:</label>
            <span class="status-value">${status.status}</span>
        </div>
        <div class="detail-row">
            <label>Last Toggled:</label>
            <span class="status-value">${lastToggled}</span>
        </div>
        <div class="detail-row">
            <label>Toggled By:</label>
            <span class="status-value">${toggledBy}</span>
        </div>
    `;
}

async function handleApiToggle(event) {
    const isChecked = event.target.checked;
    const newStatus = isChecked ? 'online' : 'offline';
    const messageDiv = document.getElementById('toggleMessage');
    
    try {
        const response = await apiFetch(`${API_URL}/status/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                toggled_by: 'User'
            })
        });
        
        if (!response.ok) throw new Error('Failed to toggle API status');
        
        const result = await response.json();
        
        // Show success message
        messageDiv.innerHTML = `
            <div class="status-message success">
                API has been turned ${newStatus.toUpperCase()}
            </div>
        `;
        
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, 3000);
        
        // Reload status
        await loadApiStatus();
    } catch (error) {
        console.error('Error toggling API:', error);
        messageDiv.innerHTML = `
            <div class="status-message error">
                Failed to toggle API status
            </div>
        `;
    }
}

// ========================
// User Management Functions
// ========================

async function loadUsers() {
    // Only show user management for superusers
    const userManagementSection = document.getElementById('userManagementSection');
    if (!state.currentUser || state.currentUser.role !== 'superuser') {
        if (userManagementSection) userManagementSection.style.display = 'none';
        return;
    }
    
    if (userManagementSection) userManagementSection.style.display = 'block';
    
    try {
        const response = await fetch(`${API_URL}/users/`, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to load users');
        
        const users = await response.json();
        renderUsersTable(users);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    const calendarLabels = {
        'both': 'Both',
        'gregorian': 'Gregorian',
        'badi': "Badí'"
    };
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                ${user.username}
                ${user.is_default ? '<span class="default-badge">Default Admin</span>' : ''}
            </td>
            <td class="role-cell">
                <span class="role-badge ${user.role}">${{'superuser': 'Super User', 'standard': 'Standard', 'viewer': 'Viewer'}[user.role] || user.role}</span>
            </td>
            <td class="calendar-cell">
                <span class="calendar-badge ${user.calendar_preference || 'both'}">${calendarLabels[user.calendar_preference] || 'Both'}</span>
            </td>
            <td>${new Date(user.created_at).toLocaleDateString()}</td>
            <td class="actions-cell">
                <button class="btn-icon edit" onclick="editUser(${user.id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                ${!user.is_default ? `
                    <button class="btn-icon delete" onclick="deleteUser(${user.id}, '${user.username}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

function openUserModal(user = null) {
    const modal = document.getElementById('userModal');
    const form = document.getElementById('userForm');
    const title = document.getElementById('userModalTitle');
    const submitBtn = document.getElementById('userSubmitBtn');
    const passwordHint = document.getElementById('passwordHint');
    const passwordInput = document.getElementById('userPassword');
    const roleSelect = document.getElementById('userRole');
    const usernameInput = document.getElementById('userUsername');
    const calendarPreferenceSelect = document.getElementById('userCalendarPreference');
    
    form.reset();
    document.getElementById('userId').value = '';
    
    if (user) {
        // Edit mode
        title.textContent = 'Edit User';
        submitBtn.textContent = 'Save Changes';
        passwordHint.style.display = 'block';
        passwordInput.required = false;
        
        document.getElementById('userId').value = user.id;
        usernameInput.value = user.username;
        roleSelect.value = user.role;
        calendarPreferenceSelect.value = user.calendar_preference || 'both';
        
        // Disable username and role for default admin, but allow calendar preference change
        if (user.is_default) {
            usernameInput.disabled = true;
            roleSelect.disabled = true;
            calendarPreferenceSelect.disabled = false;  // Always allow calendar preference change for default admin
        } else {
            usernameInput.disabled = false;
            roleSelect.disabled = false;
            calendarPreferenceSelect.disabled = false;
        }
    } else {
        // Create mode
        title.textContent = 'Add User';
        submitBtn.textContent = 'Create User';
        passwordHint.style.display = 'none';
        passwordInput.required = true;
        usernameInput.disabled = false;
        roleSelect.disabled = false;
        calendarPreferenceSelect.value = 'both';
    }
    
    openModal('userModal');
}

async function editUser(id) {
    try {
        const response = await fetch(`${API_URL}/users/${id}`, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Failed to fetch user');
        
        const user = await response.json();
        openUserModal(user);
    } catch (error) {
        console.error('Error fetching user:', error);
        alert('Failed to load user details');
    }
}

async function handleUserSubmit(e) {
    e.preventDefault();
    
    const userId = document.getElementById('userId').value;
    const username = document.getElementById('userUsername').value.trim();
    const password = document.getElementById('userPassword').value;
    const roleSelect = document.getElementById('userRole');
    const calendar_preference = document.getElementById('userCalendarPreference').value;
    
    const data = { username, calendar_preference };
    // Only include role if the field is not disabled (i.e. not the default admin)
    if (!roleSelect.disabled) data.role = roleSelect.value;
    if (password) data.password = password;
    
    try {
        let response;
        if (userId) {
            // Update
            response = await fetch(`${API_URL}/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });
        } else {
            // Create
            if (!password) {
                alert('Password is required for new users');
                return;
            }
            data.password = password;
            response = await fetch(`${API_URL}/users/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });
        }
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to save user');
            return;
        }
        
        closeModal('userModal');
        loadUsers();
    } catch (error) {
        console.error('Error saving user:', error);
        alert('Failed to save user');
    }
}

async function deleteUser(id, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(error.error || 'Failed to delete user');
            return;
        }
        
        loadUsers();
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Failed to delete user');
    }
}

async function handleChangePassword(e) {
    e.preventDefault();
    
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorDiv = document.getElementById('passwordError');
    
    errorDiv.style.display = 'none';
    
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'New passwords do not match';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (newPassword.length < 4) {
        errorDiv.textContent = 'Password must be at least 4 characters';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/auth/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            errorDiv.textContent = data.error || 'Failed to change password';
            errorDiv.style.display = 'block';
            return;
        }
        
        alert('Password changed successfully');
        closeModal('changePasswordModal');
        document.getElementById('changePasswordForm').reset();
    } catch (error) {
        console.error('Error changing password:', error);
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.style.display = 'block';
    }
}

// Clear Transactions Functionality
let pendingClearAction = null;

function initializeClearTransactions() {
    // Clear by Date
    document.getElementById('clearByDateBtn')?.addEventListener('click', async () => {
        const dateValue = document.getElementById('clearByDatePicker').value;
        if (!dateValue) {
            alert('Please select a date');
            return;
        }
        await previewAndConfirmClear('date', { date: dateValue });
    });
    
    // Clear by Period
    document.getElementById('clearByPeriodBtn')?.addEventListener('click', async () => {
        const startDate = document.getElementById('clearPeriodStart').value;
        const endDate = document.getElementById('clearPeriodEnd').value;
        
        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }
        
        if (startDate > endDate) {
            alert('Start date must be before or equal to end date');
            return;
        }
        
        await previewAndConfirmClear('period', { start_date: startDate, end_date: endDate });
    });
    
    // Clear All
    document.getElementById('clearAllBtn')?.addEventListener('click', async () => {
        await previewAndConfirmClear('all', {});
    });
    
    // Confirm Clear Button
    document.getElementById('confirmClearBtn')?.addEventListener('click', async () => {
        if (pendingClearAction) {
            await executeClear(pendingClearAction.type, pendingClearAction.params);
        }
    });
}

async function previewAndConfirmClear(type, params) {
    try {
        const queryParams = new URLSearchParams({ type, ...params });
        const response = await apiFetch(`${API_URL}/transactions/clear/preview?${queryParams}`);
        
        if (!response.ok) {
            const data = await response.json();
            alert(data.error || 'Failed to preview transactions');
            return;
        }
        
        const data = await response.json();
        
        if (data.count === 0) {
            alert('No transactions found for the selected criteria');
            return;
        }
        
        // Set pending action
        pendingClearAction = { type, params };
        
        // Update modal message
        let message = '';
        if (type === 'all') {
            message = 'Are you sure you want to delete ALL transactions?';
        } else if (type === 'date') {
            message = `Are you sure you want to delete all transactions from ${formatDateWithCalendar(params.date)}?`;
        } else if (type === 'period') {
            message = `Are you sure you want to delete all transactions from ${formatDateWithCalendar(params.start_date)} to ${formatDateWithCalendar(params.end_date)}?`;
        }
        
        document.getElementById('clearTransactionsMessage').textContent = message;
        document.getElementById('clearTransactionsCount').textContent = data.count;
        
        openModal('clearTransactionsModal');
    } catch (error) {
        console.error('Error previewing clear:', error);
        alert('Error previewing transactions to delete');
    }
}

async function executeClear(type, params) {
    try {
        let url;
        if (type === 'all') {
            url = `${API_URL}/transactions/clear/all`;
        } else if (type === 'date') {
            url = `${API_URL}/transactions/clear/by-date?date=${params.date}`;
        } else if (type === 'period') {
            url = `${API_URL}/transactions/clear/by-period?start_date=${params.start_date}&end_date=${params.end_date}`;
        }
        
        const response = await apiFetch(url, { method: 'DELETE' });
        const data = await response.json();
        
        if (!response.ok) {
            alert(data.error || 'Failed to delete transactions');
            return;
        }
        
        closeModal('clearTransactionsModal');
        pendingClearAction = null;
        
        // Clear form inputs
        document.getElementById('clearByDatePicker').value = '';
        document.getElementById('clearPeriodStart').value = '';
        document.getElementById('clearPeriodEnd').value = '';
        
        alert(`Successfully deleted ${data.deleted_count} transaction(s)`);
        
        // Reload transactions if on transactions page
        if (state.currentPage === 'transactions') {
            loadTransactions();
        } else if (state.currentPage === 'dashboard') {
            loadDashboard();
        }
    } catch (error) {
        console.error('Error clearing transactions:', error);
        alert('Error deleting transactions');
    }
}

// Upload History Management
let pendingUploadDelete = null;

async function loadUploadHistory() {
    try {
        const response = await apiFetch(`${API_URL}/uploads/`);
        if (!response.ok) throw new Error('Failed to load upload history');
        
        const uploads = await response.json();
        displayUploadHistory(uploads);
    } catch (error) {
        console.error('Error loading upload history:', error);
    }
}

function displayUploadHistory(uploads) {
    const tbody = document.getElementById('uploadHistoryBody');
    const noDataMsg = document.getElementById('noUploadsMessage');
    
    if (!uploads || uploads.length === 0) {
        tbody.innerHTML = '';
        noDataMsg.style.display = 'block';
        return;
    }
    
    noDataMsg.style.display = 'none';
    
    tbody.innerHTML = uploads.map(u => `
        <tr data-upload-id="${u.id}">
            <td class="checkbox-col">
                <input type="checkbox" class="upload-checkbox" value="${u.id}" onchange="updateUploadBulkActions()">
            </td>
            <td title="${u.original_filename}">${truncateFilename(u.original_filename, 30)}</td>
            <td><span class="file-type ${u.file_type}">${u.file_type.toUpperCase()}</span></td>
            <td>${u.file_size_formatted}</td>
            <td><strong>${u.transaction_count}</strong></td>
            <td>${u.uploaded_by}</td>
            <td>${formatDateWithCalendar(u.created_at)}</td>
            <td><span class="status-badge ${u.status}">${u.status}</span></td>
            <td>
                <div class="actions">
                    <button class="btn-icon" title="Download CSV" onclick="downloadUpload(${u.id})">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-icon delete" title="Delete" onclick="confirmDeleteUpload(${u.id}, ${u.transaction_count})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function truncateFilename(filename, maxLength) {
    if (filename.length <= maxLength) return filename;
    const ext = filename.split('.').pop();
    const name = filename.slice(0, -(ext.length + 1));
    const truncatedName = name.slice(0, maxLength - ext.length - 4) + '...';
    return `${truncatedName}.${ext}`;
}

async function downloadUpload(uploadId) {
    try {
        const response = await apiFetch(`${API_URL}/uploads/${uploadId}/download`);
        if (!response.ok) throw new Error('Failed to download');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `upload_${uploadId}_transactions.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        console.error('Error downloading upload:', error);
        alert('Error downloading file');
    }
}

function confirmDeleteUpload(uploadId, transactionCount) {
    pendingUploadDelete = { uploadId, transactionCount };
    document.getElementById('deleteUploadTransactionCount').textContent = transactionCount;
    document.getElementById('deleteUploadMessage').textContent = 
        `Are you sure you want to delete this upload and all ${transactionCount} associated transaction(s)?`;
    openModal('deleteUploadModal');
}

async function executeDeleteUpload() {
    if (!pendingUploadDelete) return;
    
    const { uploadId } = pendingUploadDelete;
    
    try {
        const response = await apiFetch(`${API_URL}/uploads/${uploadId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert(data.error || 'Failed to delete upload');
            return;
        }
        
        closeModal('deleteUploadModal');
        pendingUploadDelete = null;
        
        alert(`Successfully deleted upload and ${data.deleted_transactions} transaction(s)`);
        loadUploadHistory();
    } catch (error) {
        console.error('Error deleting upload:', error);
        alert('Error deleting upload');
    }
}

function updateUploadBulkActions() {
    const checkboxes = document.querySelectorAll('.upload-checkbox:checked');
    const bulkActions = document.getElementById('bulkUploadActions');
    const countSpan = document.getElementById('selectedUploadCount');
    
    if (checkboxes.length > 0) {
        bulkActions.style.display = 'flex';
        countSpan.textContent = `${checkboxes.length} selected`;
    } else {
        bulkActions.style.display = 'none';
    }
}

async function deleteSelectedUploads() {
    const checkboxes = document.querySelectorAll('.upload-checkbox:checked');
    const uploadIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (uploadIds.length === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${uploadIds.length} upload(s) and all their transactions? This cannot be undone.`)) {
        return;
    }
    
    try {
        let deletedCount = 0;
        let transactionCount = 0;
        
        for (const uploadId of uploadIds) {
            const response = await apiFetch(`${API_URL}/uploads/${uploadId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const data = await response.json();
                deletedCount++;
                transactionCount += data.deleted_transactions;
            }
        }
        
        alert(`Successfully deleted ${deletedCount} upload(s) and ${transactionCount} transaction(s)`);
        loadUploadHistory();
    } catch (error) {
        console.error('Error deleting uploads:', error);
        alert('Error deleting uploads');
    }
}

function initializeUploadHistoryListeners() {
    // Refresh button
    document.getElementById('refreshUploadsBtn')?.addEventListener('click', loadUploadHistory);
    
    // Select all checkbox
    document.getElementById('selectAllUploads')?.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.upload-checkbox');
        checkboxes.forEach(cb => cb.checked = e.target.checked);
        updateUploadBulkActions();
    });
    
    // Delete selected button
    document.getElementById('deleteSelectedUploadsBtn')?.addEventListener('click', deleteSelectedUploads);
    
    // Confirm delete upload button
    document.getElementById('confirmDeleteUploadBtn')?.addEventListener('click', executeDeleteUpload);
}

// ==================== Activity Logs ==================== //

let activityLogsPage = 1;
const activityLogsPerPage = 50;

async function loadActivityLogs() {
    const tbody = document.getElementById('activityLogsBody');
    if (!tbody) return;
    
    const categoryFilter = document.getElementById('activityCategoryFilter')?.value || '';
    const actionFilter = document.getElementById('activityActionFilter')?.value || '';
    const dateFilter = document.getElementById('activityDateFilter')?.value || '';
    
    try {
        let url = `/api/activity/?page=${activityLogsPage}&per_page=${activityLogsPerPage}`;
        if (categoryFilter) url += `&category=${categoryFilter}`;
        if (actionFilter) url += `&action=${actionFilter}`;
        if (dateFilter) {
            url += `&start_date=${dateFilter}&end_date=${dateFilter}`;
        }
        
        const response = await fetch(url, { credentials: 'include' });
        const data = await response.json();
        
        tbody.innerHTML = '';
        
        if (data.activities && data.activities.length > 0) {
            data.activities.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="time-cell">
                        ${formatDateTime(log.created_at)}
                        <span class="time-ago">${log.time_ago}</span>
                    </td>
                    <td class="user-cell">${escapeHtml(log.username)}</td>
                    <td><span class="action-badge ${log.action}">${log.action.replace('_', ' ')}</span></td>
                    <td><span class="category-badge">${log.category}</span></td>
                    <td class="description-cell" title="${escapeHtml(log.description)}">${escapeHtml(log.description)}</td>
                    <td class="ip-cell">${log.ip_address || '-'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="6">
                        <i class="fas fa-clipboard-list" style="font-size: 40px; color: #ddd; margin-bottom: 15px;"></i>
                        <p>No activity logs found</p>
                    </td>
                </tr>
            `;
        }
        
        // Update pagination
        updateActivityPagination(data);
        
    } catch (error) {
        console.error('Error loading activity logs:', error);
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="6">
                    <i class="fas fa-exclamation-triangle" style="color: var(--danger);"></i>
                    <p>Error loading activity logs</p>
                </td>
            </tr>
        `;
    }
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Format date with calendar preference (Gregorian or Badi)
function formatDateWithCalendar(dateString) {
    try {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Invalid Date';
        
        // Check if we should use Badi calendar
        const calendarType = state.calendarType || 'gregorian';
        
        if (calendarType === 'badi') {
            try {
                const badiDate = gregorianToBadi(date);
                return formatBadiDate(badiDate.year, badiDate.month, badiDate.day);
            } catch (error) {
                console.warn('Error formatting Badi date:', error);
                // Fallback to Gregorian if Badi conversion fails
                return date.toLocaleDateString();
            }
        } else {
            // Use Gregorian calendar
            return date.toLocaleDateString();
        }
    } catch (error) {
        console.error('Error in formatDateWithCalendar:', error);
        return 'Error';
    }
}

function updateActivityPagination(data) {
    const prevBtn = document.getElementById('activityPrevPage');
    const nextBtn = document.getElementById('activityNextPage');
    const pageInfo = document.getElementById('activityPageInfo');
    
    if (prevBtn) prevBtn.disabled = activityLogsPage <= 1;
    if (nextBtn) nextBtn.disabled = activityLogsPage >= data.pages;
    if (pageInfo) pageInfo.textContent = `Page ${data.page} of ${data.pages || 1}`;
}

async function clearOldActivityLogs() {
    const retentionDays = currentLogSettings?.retention_days || parseInt(document.getElementById('retentionDays')?.value) || 90;
    
    if (!confirm(`Are you sure you want to delete activity logs older than ${retentionDays} days?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/activity/clear?days=${retentionDays}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`Deleted ${data.deleted_count} old log entries`, 'success');
            loadActivityLogs();
        } else {
            showNotification(data.error || 'Failed to clear logs', 'error');
        }
    } catch (error) {
        console.error('Error clearing logs:', error);
        showNotification('Error clearing logs', 'error');
    }
}

function initializeActivityLogsListeners() {
    // Filter change handlers
    document.getElementById('activityCategoryFilter')?.addEventListener('change', () => {
        activityLogsPage = 1;
        loadActivityLogs();
    });
    
    document.getElementById('activityActionFilter')?.addEventListener('change', () => {
        activityLogsPage = 1;
        loadActivityLogs();
    });
    
    document.getElementById('activityDateFilter')?.addEventListener('change', () => {
        activityLogsPage = 1;
        loadActivityLogs();
    });
    
    // Refresh button
    document.getElementById('refreshActivityLogsBtn')?.addEventListener('click', loadActivityLogs);
    
    // Pagination
    document.getElementById('activityPrevPage')?.addEventListener('click', () => {
        if (activityLogsPage > 1) {
            activityLogsPage--;
            loadActivityLogs();
        }
    });
    
    document.getElementById('activityNextPage')?.addEventListener('click', () => {
        activityLogsPage++;
        loadActivityLogs();
    });
    
    // Clear old logs
    document.getElementById('clearOldLogsBtn')?.addEventListener('click', clearOldActivityLogs);
    
    // Initialize log settings listeners
    initializeLogSettingsListeners();
}

// ==================== Log Settings ==================== //

let currentLogSettings = null;

async function loadLogSettings() {
    try {
        const response = await fetch('/api/activity/settings', { credentials: 'include' });
        if (response.ok) {
            currentLogSettings = await response.json();
            populateLogSettingsUI(currentLogSettings);
        }
    } catch (error) {
        console.error('Error loading log settings:', error);
    }
}

function populateLogSettingsUI(settings) {
    // Master toggle
    const loggingToggle = document.getElementById('loggingEnabledToggle');
    if (loggingToggle) {
        loggingToggle.checked = settings.logging_enabled;
        updateLogSettingsVisibility(settings.logging_enabled);
    }
    
    // Category checkboxes
    const categoryCheckboxes = document.querySelectorAll('#categoryCheckboxes input[type="checkbox"]');
    categoryCheckboxes.forEach(cb => {
        cb.checked = settings.enabled_categories.includes(cb.value);
    });
    
    // Action checkboxes
    const actionCheckboxes = document.querySelectorAll('#actionCheckboxes input[type="checkbox"]');
    actionCheckboxes.forEach(cb => {
        cb.checked = settings.enabled_actions.includes(cb.value);
    });
    
    // Retention settings
    const retentionDays = document.getElementById('retentionDays');
    if (retentionDays) retentionDays.value = settings.retention_days;
    
    const autoCleanup = document.getElementById('autoCleanupToggle');
    if (autoCleanup) autoCleanup.checked = settings.auto_cleanup;
    
    // Export format
    const exportFormat = document.getElementById('exportFormat');
    if (exportFormat) exportFormat.value = settings.export_format;
    
    // File logging settings
    const fileLoggingToggle = document.getElementById('fileLoggingToggle');
    if (fileLoggingToggle) {
        fileLoggingToggle.checked = settings.file_logging_enabled;
        toggleFileDestinationSettings(settings.file_logging_enabled);
    }
    
    // Destination type
    const destinationType = document.getElementById('destinationType');
    if (destinationType) {
        destinationType.value = settings.log_destination_type;
        updateDestinationConfig(settings.log_destination_type);
    }
    
    // Local path
    const localLogPath = document.getElementById('localLogPath');
    if (localLogPath) localLogPath.value = settings.log_path || '';
    
    // SMB settings
    document.getElementById('smbServer')?.setAttribute('value', settings.smb_server || '');
    document.getElementById('smbShare')?.setAttribute('value', settings.smb_share || '');
    document.getElementById('smbDomain')?.setAttribute('value', settings.smb_domain || '');
    document.getElementById('smbUsername')?.setAttribute('value', settings.smb_username || '');
    
    // NFS settings
    document.getElementById('nfsServer')?.setAttribute('value', settings.nfs_server || '');
    document.getElementById('nfsExport')?.setAttribute('value', settings.nfs_export || '');
    document.getElementById('nfsMountOptions')?.setAttribute('value', settings.nfs_mount_options || '');
}

function updateLogSettingsVisibility(enabled) {
    const settingsGroup = document.getElementById('logSettingsGroup');
    if (settingsGroup) {
        if (enabled) {
            settingsGroup.classList.remove('disabled');
        } else {
            settingsGroup.classList.add('disabled');
        }
    }
}

function toggleFileDestinationSettings(show) {
    const settings = document.getElementById('fileDestinationSettings');
    if (settings) {
        settings.style.display = show ? 'block' : 'none';
    }
}

function updateDestinationConfig(type) {
    document.getElementById('localPathConfig').style.display = type === 'local' ? 'block' : 'none';
    document.getElementById('smbConfig').style.display = type === 'smb' ? 'block' : 'none';
    document.getElementById('nfsConfig').style.display = type === 'nfs' ? 'block' : 'none';
}

async function saveLogSettings() {
    const settings = {
        logging_enabled: document.getElementById('loggingEnabledToggle')?.checked || false,
        enabled_categories: Array.from(document.querySelectorAll('#categoryCheckboxes input:checked')).map(cb => cb.value),
        enabled_actions: Array.from(document.querySelectorAll('#actionCheckboxes input:checked')).map(cb => cb.value),
        retention_days: parseInt(document.getElementById('retentionDays')?.value) || 90,
        auto_cleanup: document.getElementById('autoCleanupToggle')?.checked || false,
        export_format: document.getElementById('exportFormat')?.value || 'csv',
        file_logging_enabled: document.getElementById('fileLoggingToggle')?.checked || false,
        log_destination_type: document.getElementById('destinationType')?.value || 'local',
        log_path: document.getElementById('localLogPath')?.value || '',
        smb_server: document.getElementById('smbServer')?.value || '',
        smb_share: document.getElementById('smbShare')?.value || '',
        smb_domain: document.getElementById('smbDomain')?.value || '',
        smb_username: document.getElementById('smbUsername')?.value || '',
        smb_password: document.getElementById('smbPassword')?.value || '',
        nfs_server: document.getElementById('nfsServer')?.value || '',
        nfs_export: document.getElementById('nfsExport')?.value || '',
        nfs_mount_options: document.getElementById('nfsMountOptions')?.value || ''
    };
    
    try {
        const response = await fetch('/api/activity/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Log settings saved successfully', 'success');
            currentLogSettings = data.settings;
        } else {
            showNotification(data.error || 'Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Error saving log settings:', error);
        showNotification('Error saving settings', 'error');
    }
}

async function exportLogs() {
    const format = document.getElementById('exportFormat')?.value || 'csv';
    const category = document.getElementById('activityCategoryFilter')?.value || '';
    const action = document.getElementById('activityActionFilter')?.value || '';
    const date = document.getElementById('activityDateFilter')?.value || '';
    
    let url = `/api/activity/export?format=${format}`;
    if (category) url += `&category=${category}`;
    if (action) url += `&action=${action}`;
    if (date) url += `&start_date=${date}&end_date=${date}`;
    
    try {
        window.location.href = url;
        showNotification('Exporting logs...', 'success');
    } catch (error) {
        showNotification('Failed to export logs', 'error');
    }
}

async function testLogDestination() {
    try {
        const response = await fetch('/api/activity/test-destination', {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.error || data.message || 'Connection test failed', 'error');
        }
    } catch (error) {
        showNotification('Error testing destination', 'error');
    }
}

async function saveLogsToFile() {
    try {
        const response = await fetch('/api/activity/save-to-file', {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.error || 'Failed to save logs', 'error');
        }
    } catch (error) {
        showNotification('Error saving logs to file', 'error');
    }
}

function initializeLogSettingsListeners() {
    // Master toggle
    document.getElementById('loggingEnabledToggle')?.addEventListener('change', (e) => {
        updateLogSettingsVisibility(e.target.checked);
    });
    
    // File logging toggle
    document.getElementById('fileLoggingToggle')?.addEventListener('change', (e) => {
        toggleFileDestinationSettings(e.target.checked);
    });
    
    // Destination type change
    document.getElementById('destinationType')?.addEventListener('change', (e) => {
        updateDestinationConfig(e.target.value);
    });
    
    // Save settings button
    document.getElementById('saveLogSettingsBtn')?.addEventListener('click', saveLogSettings);
    
    // Export logs button
    document.getElementById('exportLogsBtn')?.addEventListener('click', exportLogs);
    
    // Test destination button
    document.getElementById('testDestinationBtn')?.addEventListener('click', testLogDestination);
    
    // Save logs to file button
    document.getElementById('saveLogsToFileBtn')?.addEventListener('click', saveLogsToFile);

    // --- Settings Backup/Restore ---
    document.getElementById('saveSettingsBtn')?.addEventListener('click', async () => {
        showSettingsBackupMessage('Saving settings...', 'info');
        // For now, just show a message (settings are always saved to DB)
        setTimeout(() => showSettingsBackupMessage('Settings saved to database.', 'success'), 800);
    });

    document.getElementById('backupSettingsBtn')?.addEventListener('click', async () => {
        showSettingsBackupMessage('Preparing backup...', 'info');
        try {
            const resp = await fetch('/api/status/settings/backup', { credentials: 'include' });
            if (!resp.ok) throw new Error('Failed to download backup');
            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'settings-backup.json';
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showSettingsBackupMessage('Settings backup downloaded.', 'success');
        } catch (e) {
            showSettingsBackupMessage('Failed to back up settings: ' + e, 'error');
        }
    });

    document.getElementById('restoreSettingsInput')?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        showSettingsBackupMessage('Restoring settings...', 'info');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const resp = await fetch('/api/status/settings/restore', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            const data = await resp.json();
            if (resp.ok && data.success) {
                showSettingsBackupMessage('Settings restored successfully. Please reload the page.', 'success');
            } else {
                showSettingsBackupMessage('Restore failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (e) {
            showSettingsBackupMessage('Restore failed: ' + e, 'error');
        }
    });

    function showSettingsBackupMessage(msg, type) {
        const el = document.getElementById('settingsBackupMessage');
        if (!el) return;
        el.textContent = msg;
        el.className = type ? 'msg-' + type : '';
    }

    // --- Reset Profile ---
    document.getElementById('resetProfileBtn')?.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to reset your profile to default? This will delete all data except the admin user.')) return;
        showSettingsBackupMessage('Resetting profile...', 'info');
        try {
            const resp = await fetch('/api/status/settings/reset', { method: 'POST', credentials: 'include' });
            const data = await resp.json();
            if (resp.ok && data.success) {
                showSettingsBackupMessage('Profile reset. Please reload the page.', 'success');
            } else {
                showSettingsBackupMessage('Reset failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (e) {
            showSettingsBackupMessage('Reset failed: ' + e, 'error');
        }
    });

    // --- Back Up Database ---
    document.getElementById('backupDbBtn')?.addEventListener('click', async () => {
        showSettingsBackupMessage('Preparing database backup...', 'info');
        try {
            const resp = await fetch('/api/status/settings/db/backup', { credentials: 'include' });
            if (!resp.ok) throw new Error('Failed to download database');
            const blob = await resp.blob();
            // Prompt user to save file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'expense_tracker.db';
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 100);
            showSettingsBackupMessage('Database backup downloaded. If you did not see a file save dialog, please check your browser settings.', 'success');
        } catch (e) {
            showSettingsBackupMessage(
                'Failed to back up database: ' + e +
                '. If the download does not start, please manually save the database file from <b>/app/backend/data/expense_tracker.db</b> in your Docker container.',
                'error'
            );
        }
    });

    // --- Restore Database ---
    document.getElementById('restoreDbInput')?.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        showSettingsBackupMessage('Restoring database...', 'info');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const resp = await fetch('/api/status/settings/db/restore', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });
            const data = await resp.json();
            if (resp.ok && data.success) {
                showSettingsBackupMessage('Database restored. Please restart the app.', 'success');
            } else {
                showSettingsBackupMessage('Restore failed: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (e) {
            showSettingsBackupMessage('Restore failed: ' + e, 'error');
        }
    });
    
    // Load settings on init
    loadLogSettings();
}

// Modal Management Functions
function openModal(modalId) {
    console.log('Opening modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        // Focus first input in modal
        const firstInput = modal.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    } else {
        console.error('Modal not found:', modalId);
    }
}

function closeModal(modalId) {
    console.log('Closing modal:', modalId);
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
    } else {
        console.error('Modal not found:', modalId);
    }
}

// Notification Functions
function showNotification(message, type = 'info', duration = 3000) {
    console.log('Notification:', message, type);
    
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateX(400px);
        transition: transform 0.3s ease-in-out;
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#27ae60';
            break;
        case 'error':
            notification.style.backgroundColor = '#e74c3c';
            break;
        case 'warning':
            notification.style.backgroundColor = '#f39c12';
            break;
        default:
            notification.style.backgroundColor = '#3498db';
    }
    
    // Add to document
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, duration);
}
