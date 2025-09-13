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
});

// Form validation
function validateInputs() {
    const area = parseFloat(document.getElementById('area').value);
    const seats = parseInt(document.getElementById('seats').value);
    
    const isValid = area > 0 && seats >= 0;
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

// Display checklist section
function displayChecklist(checklist) {
    const checklistContent = document.getElementById('checklistContent');
    
    if (!checklist || checklist.length === 0) {
        checklistContent.innerHTML = '<p>לא נמצאו דרישות רגולטוריות.</p>';
        return;
    }
    
    const checklistHTML = checklist.map(item => `
        <div class="checklist-item">
            <div class="checklist-category">${item.category}</div>
            <h4>${item.title}</h4>
            <div class="checklist-note">${item.note || ''}</div>
        </div>
    `).join('');
    
    checklistContent.innerHTML = checklistHTML;
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
    
    // Actions section
    if (aiReport.actions && aiReport.actions.length > 0) {
        html += `
            <div class="ai-section">
                <h4>📋 פעולות נדרשות</h4>
                ${aiReport.actions.map(action => `
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
                `).join('')}
            </div>
        `;
    }
    
    // Risks section
    if (aiReport.potential_risks && aiReport.potential_risks.length > 0) {
        html += `
            <div class="ai-section">
                <h4>⚠️ סיכונים פוטנציאליים</h4>
                ${aiReport.potential_risks.map(risk => `
                    <div class="risk-item">
                        <div class="impact-badge impact-${risk.impact || 'medium'}">
                            השפעה: ${getImpactText(risk.impact)}
                        </div>
                        <h5>${risk.risk_type || 'סיכון כללי'}</h5>
                        <p><strong>תיאור:</strong> ${risk.description}</p>
                        <p><strong>דרכי התמודדות:</strong> ${risk.mitigation}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Tips section
    if (aiReport.tips && aiReport.tips.length > 0) {
        html += `
            <div class="ai-section">
                <h4>💡 טיפים מועילים</h4>
                ${aiReport.tips.map(tip => `
                    <div class="tip-item">
                        <h5>${tip.category || 'טיפ כללי'}</h5>
                        <p><strong>טיפ:</strong> ${tip.tip}</p>
                        <p><strong>תועלת:</strong> ${tip.benefit}</p>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Budget planning section
    if (aiReport.budget_planning) {
        html += `
            <div class="ai-section">
                <h4>💰 תכנון תקציב</h4>
                ${aiReport.budget_planning.fixed_costs && aiReport.budget_planning.fixed_costs.length > 0 ? 
                    `<p><strong>עלויות חד פעמיות:</strong></p>
                     <ul>${aiReport.budget_planning.fixed_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>` : ''}
                ${aiReport.budget_planning.recurring_costs && aiReport.budget_planning.recurring_costs.length > 0 ? 
                    `<p><strong>עלויות שוטפות:</strong></p>
                     <ul>${aiReport.budget_planning.recurring_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>` : ''}
                ${aiReport.budget_planning.optional_costs && aiReport.budget_planning.optional_costs.length > 0 ? 
                    `<p><strong>עלויות אופציונליות:</strong></p>
                     <ul>${aiReport.budget_planning.optional_costs.map(cost => `<li>${cost}</li>`).join('')}</ul>` : ''}
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
