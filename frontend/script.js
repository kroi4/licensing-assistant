// Application will use ApiService from service.js
// Configuration is loaded from clinet_config

// DOM Elements
const form = document.getElementById('businessForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.querySelector('.btn-text');
const loadingSpinner = document.querySelector('.loading-spinner');
const resultsContainer = document.getElementById('results');
const errorContainer = document.getElementById('error');

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    form.addEventListener('submit', handleFormSubmit);
    
    // Add input validation
    const areaInput = document.getElementById('area');
    const seatsInput = document.getElementById('seats');
    
    areaInput.addEventListener('input', validateInputs);
    seatsInput.addEventListener('input', validateInputs);

    // Add event listeners for all feature checkboxes
    const featureCheckboxes = document.querySelectorAll('input[name="features"]');
    featureCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', validateInputs);
    });
    
    // Initial validation
    validateInputs();
});

// Form validation
function validateInputs() {
    const area = parseFloat(document.getElementById('area').value);
    const seats = parseInt(document.getElementById('seats').value);
    
    // Check if at least one feature is selected
    const selectedFeatures = document.querySelectorAll('input[name="features"]:checked');
    const hasFeature = selectedFeatures.length > 0;
    
    const isValid = area > 0 && seats >= 0 && hasFeature;
    submitBtn.disabled = !isValid;
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Early validation before showing loading state
    const formData = collectFormData();
    if (!validateFormData(formData)) {
        displayError('נתונים לא תקינים. אנא בדוק את הקלט.');
        return;
    }
    
    // Show loading state only after validation passes
    setLoadingState(true);
    hideResults();
    hideError();
    
    try {
        // Check if ApiService is available
        if (!window.ApiService) {
            throw new Error('שירות ה-API לא זמין. אנא רענן את הדף.');
        }
        
        // Use the API service layer
        const result = await window.ApiService.assessBusiness(formData);
        displayResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        displayError(error.message);
    } finally {
        setLoadingState(false);
    }
}

// Collect form data
function collectFormData() {
    const area = parseFloat(document.getElementById('area').value);
    const seats = parseInt(document.getElementById('seats').value);
    
    // Collect selected features
    const featureCheckboxes = document.querySelectorAll('input[name="features"]:checked');
    const features = Array.from(featureCheckboxes).map(cb => cb.value);
    
    return {
        area: area,
        seats: seats,
        features: features
    };
}

// Validate form data
function validateFormData(data) {
    return data.area > 0 && data.seats >= 0 && Array.isArray(data.features);
}

// Set loading state
function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    
    if (isLoading) {
        btnText.style.display = 'none';
        loadingSpinner.style.display = 'inline-block';
    } else {
        btnText.style.display = 'inline-block';
        loadingSpinner.style.display = 'none';
    }
}

// Display results
function displayResults(data) {
    hideError();
    
    // Reset pagination counters on new results
    checklistShowCount = PAGE_SIZE;
    actionsShowCount = PAGE_SIZE;
    risksShowCount = PAGE_SIZE;
    tipsShowCount = PAGE_SIZE;

    // Display summary
    displaySummary(data.summary);
    
    // Display checklist
    displayChecklist(data.checklist);
    
    // Display AI report
    if (data.ai_report) {
        displayAIReport(data.ai_report);
    }
    
    // Show results container
    resultsContainer.style.display = 'block';
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

// Display summary section
function displaySummary(summary) {
    const summaryContent = document.getElementById('summaryContent');
    
    const featuresText = summary.features.length > 0 
        ? summary.features.join(', ') 
        : 'אין מאפיינים מיוחדים';
    
    summaryContent.innerHTML = `
        <div class="summary-item">
            <span class="summary-label">סוג העסק:</span>
            <span class="summary-value">${summary.type === 'restaurant' ? 'מסעדה/בית אוכל' : summary.type}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">שטח:</span>
            <span class="summary-value">${summary.area} מ"ר</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">מקומות ישיבה:</span>
            <span class="summary-value">${summary.seats}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">מאפיינים מיוחדים:</span>
            <span class="summary-value">${featuresText}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">מסלול כבאות:</span>
            <span class="summary-value">${summary.fire_track}</span>
        </div>
        <div class="summary-item">
            <span class="summary-label">דרישות משטרה:</span>
            <span class="summary-value">${summary.police}</span>
        </div>
    `;
}

// Global state for pagination (per section)
const PAGE_SIZE = 10;
let checklistShowCount = PAGE_SIZE;
let actionsShowCount = PAGE_SIZE;
let risksShowCount = PAGE_SIZE;
let tipsShowCount = PAGE_SIZE;

// Display checklist section with show more functionality
function displayChecklist(checklist) {
    const checklistContent = document.getElementById('checklistContent');
    
    if (!checklist || checklist.length === 0) {
        checklistContent.innerHTML = '<p>לא נמצאו דרישות רגולטוריות.</p>';
        return;
    }
    
    const LIMIT = checklistShowCount;
    const itemsToShow = checklist.slice(0, LIMIT);
    
    const checklistHTML = itemsToShow.map(item => {
        // Filter out technical notes that shouldn't be shown to users
        let note = item.note || '';
        if (note.includes('מחולץ מקובץ Word') || note.includes('מחולץ מקובץ PDF')) {
            note = ''; // Remove technical extraction notes
        }
        
        return `
            <div class="checklist-item">
                <div class="checklist-category">${item.category}</div>
                <h4>${item.title}</h4>
                ${note ? `<div class="checklist-note">${note}</div>` : ''}
            </div>
        `;
    }).join('');
    
    let showMoreButton = '';
    if (checklist.length > LIMIT) {
        const remaining = checklist.length - LIMIT;
        const nextBatch = Math.min(PAGE_SIZE, remaining);
        showMoreButton = `
            <div class="show-more-controls">
                <button onclick="showMoreChecklist()" class="show-more-btn">
                    הצג עוד ${nextBatch} (מתוך ${remaining} נוספים) ⬇️
                </button>
                <button onclick="showAllChecklist()" class="show-all-btn">
                    הצג הכל
                </button>
            </div>
        `;
    } else if (LIMIT > PAGE_SIZE) {
        showMoreButton = `
            <div class="show-more-controls">
                <button onclick="showLessChecklist()" class="show-less-btn">
                    הצג פחות ⬆️
                </button>
            </div>
        `;
    }
    
    checklistContent.innerHTML = checklistHTML + showMoreButton;
    
    // Store globally for toggle function
    window.currentChecklist = checklist;
}

function showMoreChecklist() {
    checklistShowCount = Math.min(checklistShowCount + PAGE_SIZE, window.currentChecklist.length);
    displayChecklist(window.currentChecklist);
}

function showAllChecklist() {
    checklistShowCount = window.currentChecklist.length;
    displayChecklist(window.currentChecklist);
}

function showLessChecklist() {
    checklistShowCount = PAGE_SIZE;
    displayChecklist(window.currentChecklist);
}

function showMoreActions() {
    actionsShowCount = Math.min(actionsShowCount + PAGE_SIZE, (window.currentActions || []).length);
    displayAIReport(window.currentAIReport);
}

function showAllActions() {
    actionsShowCount = (window.currentActions || []).length;
    displayAIReport(window.currentAIReport);
}

function showLessActions() {
    actionsShowCount = PAGE_SIZE;
    displayAIReport(window.currentAIReport);
}

function showMoreRisks() {
    risksShowCount = Math.min(risksShowCount + PAGE_SIZE, (window.currentAIReport?.potential_risks || []).length);
    displayAIReport(window.currentAIReport);
}

function showAllRisks() {
    risksShowCount = (window.currentAIReport?.potential_risks || []).length;
    displayAIReport(window.currentAIReport);
}

function showLessRisks() {
    risksShowCount = PAGE_SIZE;
    displayAIReport(window.currentAIReport);
}

function showMoreTips() {
    tipsShowCount = Math.min(tipsShowCount + PAGE_SIZE, (window.currentAIReport?.tips || []).length);
    displayAIReport(window.currentAIReport);
}

function showAllTips() {
    tipsShowCount = (window.currentAIReport?.tips || []).length;
    displayAIReport(window.currentAIReport);
}

function showLessTips() {
    tipsShowCount = PAGE_SIZE;
    displayAIReport(window.currentAIReport);
}

// Display AI report section
function displayAIReport(aiReport) {
    const aiReportContent = document.getElementById('aiReportContent');
    
    if (!aiReport) {
        aiReportContent.innerHTML = '<p>דוח AI לא זמין כרגע.</p>';
        return;
    }
    
    let html = '';
    
    // Summary section
    if (aiReport.summary) {
        const complexityClass = `complexity-${aiReport.summary.complexity_level || 'medium'}`;
        html += `
            <div class="ai-summary">
                <h4>הערכה כללית</h4>
                <p>${aiReport.summary.assessment || 'לא סופקה הערכה'}</p>
                <div class="complexity-badge ${complexityClass}">
                    רמת מורכבות: ${getComplexityText(aiReport.summary.complexity_level)}
                </div>
                <p><strong>זמן משוער:</strong> ${aiReport.summary.estimated_time || 'לא סופק'}</p>
                ${aiReport.summary.key_challenges && aiReport.summary.key_challenges.length > 0 ? 
                    `<p><strong>אתגרים עיקריים:</strong> ${aiReport.summary.key_challenges.join(', ')}</p>` : ''}
            </div>
        `;
    }
    
    // Actions section with show more functionality
    if (aiReport.actions && aiReport.actions.length > 0) {
        const ACTIONS_LIMIT = actionsShowCount;
        const actionsToShow = aiReport.actions.slice(0, ACTIONS_LIMIT);
        
        let actionsHTML = actionsToShow.map(action => `
            <div class="action-item">
                <div class="priority-badge priority-${action.priority || 'medium'}">
                    עדיפות: ${getPriorityText(action.priority)}
                </div>
                <h5>${action.title}</h5>
                <p><strong>קטגוריה:</strong> ${action.category || 'כללי'}</p>
                ${action.required_professionals && action.required_professionals.length > 0 ? 
                    `<p><strong>אנשי מקצוע נדרשים:</strong> ${action.required_professionals.join(', ')}</p>` : ''}
                ${action.estimated_cost_range ? 
                    `<p><strong>טווח עלויות:</strong> ${action.estimated_cost_range}</p>` : ''}
                <p>${action.explanation || ''}</p>
            </div>
        `).join('');
        
        // Add show more button if needed
        if (aiReport.actions.length > ACTIONS_LIMIT) {
            const remaining = aiReport.actions.length - ACTIONS_LIMIT;
            const nextBatch = Math.min(PAGE_SIZE, remaining);
            actionsHTML += `
                <div class="show-more-controls">
                    <button onclick="showMoreActions()" class="show-more-btn">
                        הצג עוד ${nextBatch} (מתוך ${remaining} נוספים) ⬇️
                    </button>
                    <button onclick="showAllActions()" class="show-all-btn">
                        הצג הכל
                    </button>
                </div>
            `;
        } else if (ACTIONS_LIMIT > PAGE_SIZE) {
            actionsHTML += `
                <div class="show-more-controls">
                    <button onclick="showLessActions()" class="show-less-btn">
                        הצג פחות ⬆️
                    </button>
                </div>
            `;
        }
        
        html += `
            <div class="ai-section">
                <h4>📋 פעולות נדרשות</h4>
                ${actionsHTML}
            </div>
        `;
        
        // Store globally for toggle function
        window.currentActions = aiReport.actions;
    }
    
    // Risks section with show more functionality
    if (aiReport.potential_risks && aiReport.potential_risks.length > 0) {
        const RISKS_LIMIT = risksShowCount;
        const risksToShow = aiReport.potential_risks.slice(0, RISKS_LIMIT);
        
        let risksHTML = risksToShow.map(risk => `
            <div class="risk-item">
                <div class="impact-badge impact-${risk.impact || 'medium'}">
                    השפעה: ${getImpactText(risk.impact)}
                </div>
                <h5>${risk.risk_type || 'סיכון כללי'}</h5>
                <p><strong>תיאור:</strong> ${risk.description}</p>
                <p><strong>דרכי התמודדות:</strong> ${risk.mitigation}</p>
            </div>
        `).join('');
        
        // Add show more button for risks
        if (aiReport.potential_risks.length > RISKS_LIMIT) {
            const remaining = aiReport.potential_risks.length - RISKS_LIMIT;
            const nextBatch = Math.min(PAGE_SIZE, remaining);
            risksHTML += `
                <div class="show-more-controls">
                    <button onclick="showMoreRisks()" class="show-more-btn">
                        הצג עוד ${nextBatch} (מתוך ${remaining} נוספים) ⬇️
                    </button>
                    <button onclick="showAllRisks()" class="show-all-btn">
                        הצג הכל
                    </button>
                </div>
            `;
        } else if (RISKS_LIMIT > PAGE_SIZE) {
            risksHTML += `
                <div class="show-more-controls">
                    <button onclick="showLessRisks()" class="show-less-btn">
                        הצג פחות ⬆️
                    </button>
                </div>
            `;
        }
        
        html += `
            <div class="ai-section">
                <h4>⚠️ סיכונים פוטנציאליים</h4>
                ${risksHTML}
            </div>
        `;
    }
    
    // Tips section with show more functionality
    if (aiReport.tips && aiReport.tips.length > 0) {
        const TIPS_LIMIT = tipsShowCount;
        const tipsToShow = aiReport.tips.slice(0, TIPS_LIMIT);
        
        let tipsHTML = tipsToShow.map(tip => `
            <div class="tip-item">
                <h5>${tip.category || 'טיפ כללי'}</h5>
                <p><strong>טיפ:</strong> ${tip.tip}</p>
                <p><strong>תועלת:</strong> ${tip.benefit}</p>
            </div>
        `).join('');
        
        // Add show more button for tips
        if (aiReport.tips.length > TIPS_LIMIT) {
            const remaining = aiReport.tips.length - TIPS_LIMIT;
            const nextBatch = Math.min(PAGE_SIZE, remaining);
            tipsHTML += `
                <div class="show-more-controls">
                    <button onclick="showMoreTips()" class="show-more-btn">
                        הצג עוד ${nextBatch} (מתוך ${remaining} נוספים) ⬇️
                    </button>
                    <button onclick="showAllTips()" class="show-all-btn">
                        הצג הכל
                    </button>
                </div>
            `;
        } else if (TIPS_LIMIT > PAGE_SIZE) {
            tipsHTML += `
                <div class="show-more-controls">
                    <button onclick="showLessTips()" class="show-less-btn">
                        הצג פחות ⬆️
                    </button>
                </div>
            `;
        }
        
        html += `
            <div class="ai-section">
                <h4>💡 טיפים מועילים</h4>
                ${tipsHTML}
            </div>
        `;
    }
    
    // Budget planning section - simplified and cleaner
    if (aiReport.budget_planning) {
        html += `
            <div class="ai-section">
                <h4>💰 תכנון תקציב</h4>
                
                ${aiReport.budget_planning.fixed_costs && aiReport.budget_planning.fixed_costs.length > 0 ? 
                    `<div class="budget-category">
                        <h5>💵 עלויות חד פעמיות</h5>
                        <ul class="budget-list">${aiReport.budget_planning.fixed_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>
                    </div>` : ''}
                
                ${aiReport.budget_planning.recurring_costs && aiReport.budget_planning.recurring_costs.length > 0 ? 
                    `<div class="budget-category">
                        <h5>🔄 עלויות שוטפות</h5>
                        <ul class="budget-list">${aiReport.budget_planning.recurring_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>
                    </div>` : ''}
                
                ${aiReport.budget_planning.optional_costs && aiReport.budget_planning.optional_costs.length > 0 ? 
                    `<div class="budget-category">
                        <h5>⭐ עלויות אופציונליות</h5>
                        <ul class="budget-list">${aiReport.budget_planning.optional_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>
                    </div>` : ''}
                
                <div class="budget-note">
                    <p><strong>💡 הערה:</strong> המחירים המדויקים ייקבעו לפי הצעות מחיר ממומחים מוסמכים</p>
                </div>
            </div>
        `;
    }
    
    // Open questions section
    if (aiReport.open_questions && aiReport.open_questions.length > 0) {
        html += `
            <div class="ai-section">
                <h4>❓ שאלות לבירור</h4>
                <ul>
                    ${aiReport.open_questions.map(question => `<li>${question}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    aiReportContent.innerHTML = html;
    
    // Store globally for toggle functions
    window.currentAIReport = aiReport;
}

// Helper functions for text conversion
function getComplexityText(level) {
    const levels = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה'
    };
    return levels[level] || 'בינונית';
}

function getPriorityText(priority) {
    const priorities = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה'
    };
    return priorities[priority] || 'בינונית';
}

function getImpactText(impact) {
    const impacts = {
        'high': 'גבוהה',
        'medium': 'בינונית',
        'low': 'נמוכה'
    };
    return impacts[impact] || 'בינונית';
}

// Display error
function displayError(message) {
    hideResults();
    
    const errorContent = document.getElementById('errorContent');
    errorContent.innerHTML = `<p>${message}</p>`;
    
    errorContainer.style.display = 'block';
    errorContainer.scrollIntoView({ behavior: 'smooth' });
}

// Hide results
function hideResults() {
    resultsContainer.style.display = 'none';
}

// Hide error
function hideError() {
    errorContainer.style.display = 'none';
}
