document.addEventListener('DOMContentLoaded', function() {
    const commandInput = document.getElementById('commandInput');
    const executeBtn = document.getElementById('executeBtn');
    const columnSelect = document.getElementById('columnSelect');
    const operationSelect = document.getElementById('operationSelect');
    const dropdownExecuteBtn = document.getElementById('dropdownExecuteBtn');
    const resultsContainer = document.getElementById('resultsContainer');
    
    // Get filename from URL or template variable
    const filename = window.location.pathname.split('/').pop();
    
    // Command input execution
    executeBtn.addEventListener('click', executeCommand);
    commandInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') executeCommand();
    });
    
    // Dropdown execution
    dropdownExecuteBtn.addEventListener('click', executeDropdown);
    
    function executeCommand() {
        const command = commandInput.value.trim();
        if (!command) return;
        
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                command: command,
                filename: filename
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayResults(data.result, data.command);
            } else {
                showError(data.error);
            }
        })
        .catch(error => showError(error.message));
    }
    
    function executeDropdown() {
        const column = columnSelect.value;
        const operation = operationSelect.value;
        
        if (!column) {
            showError('Please select a column');
            return;
        }
        
        const command = `${operation} of ${column}`;
        commandInput.value = command;
        executeCommand();
    }
    
function displayResults(results, command) {
    let html = `<h3>Results for: "${command}"</h3><div class="results-grid">`;
    
    for (const [column, stats] of Object.entries(results)) {
        html += `<div class="result-card"><h4>${column}</h4><ul>`;
        
        if (stats.error) {
            html += `<li class="error-message"><i class="fas fa-exclamation-circle"></i> ${stats.error}</li>`;
        } else {
            for (const [stat, value] of Object.entries(stats)) {
                let displayValue;
                if (Array.isArray(value)) {
                    displayValue = value.join(', ');
                } else if (typeof value === 'number') {
                    displayValue = Number.isInteger(value) ? value.toString() : value.toFixed(2);
                } else {
                    displayValue = value;
                }
                html += `<li><strong>${stat}:</strong> ${displayValue}</li>`;
            }
        }
        
        html += `</ul></div>`;
    }
    
    html += `</div>`;
    resultsContainer.innerHTML = html;
}
    
function showError(message) {
    resultsContainer.innerHTML = `
        <div class="error">
            <i class="fas fa-exclamation-circle"></i>
            <p>${message}</p>
            <p>Try commands like:</p>
            <ul class="suggestions">
                <li>"mean of age"</li>
                <li>"median of salary"</li>
                <li>"mode of country"</li>
                <li>"min of price"</li>
                <li>"max of score"</li>
                <li>"std of temperature"</li>
            </ul>
        </div>
    `;
}
});

document.addEventListener('DOMContentLoaded', function() {
    // Your existing analysis code...
    
    // Add download progress indicators
    document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Preparing...';
            
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 3000);
        });
    });
    
    // Add click tracking (optional)
    document.querySelectorAll('.download-options a').forEach(link => {
        link.addEventListener('click', function() {
            const downloadType = this.textContent.trim();
            console.log(`Download initiated: ${downloadType}`);
            // You could add analytics here
        });
    });
});