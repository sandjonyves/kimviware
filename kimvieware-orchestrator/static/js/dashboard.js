// Initialize Bootstrap Modal
let jobDetailModal;
document.addEventListener('DOMContentLoaded', () => {
    const modalElement = document.getElementById('jobModal');
    jobDetailModal = new bootstrap.Modal(modalElement);

    // Hide all sections except the default one on initial load
    document.querySelectorAll('div[id$="Section"]').forEach(el => {
        if (el.id !== 'uploadSection') { // Default to showing uploadSection
            el.style.display = 'none';
        }
    });

    loadJobs();
    loadServices();
    loadStats();

    // Refresh data every 2 seconds (polling)
    setInterval(() => {
        loadJobs();
        loadStats();
    }, 2000);

    // File input change for visual feedback
    document.getElementById('fileInput').addEventListener('change', (e) => {
        if (e.target.files[0]) {
            updateFileName(e.target.files[0]);
        }
    });

    // Form submission
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);

    // Bootstrap tab activation for stats
    const statsTabEl = document.getElementById('statsTab');
    if (statsTabEl) {
        statsTabEl.addEventListener('shown.bs.tab', event => {
            console.log(`Switched to tab: ${event.target.id}`);
        });
    }
});

// Helper function for alerts
function showAlert(type, message) {
    const alertElement = document.getElementById(`alert${type.charAt(0).toUpperCase() + type.slice(1)}`);
    if (alertElement) {
        alertElement.innerHTML = `<i class="bi bi-info-circle me-2"></i> ${message}`;
        alertElement.classList.remove('d-none');
        alertElement.classList.add('show');
        setTimeout(() => {
            alertElement.classList.remove('show');
            alertElement.classList.add('d-none');
        }, 5000);
    }
}

function updateFileName(file) {
    const fileNameEl = document.getElementById('fileName');
    if (fileNameEl) {
        fileNameEl.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        fileNameEl.style.display = 'block';
    }
}

async function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        showAlert('error', '❌ Veuillez sélectionner un fichier');
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('progressBar');
    const progressFill = document.getElementById('progressFill');

    submitBtn.disabled = true;
    progressBar.classList.remove('d-none'); // Show progress bar
    progressFill.style.width = '0%';
    progressFill.setAttribute('aria-valuenow', 0);

    const formData = new FormData();
    formData.append('file', file);

    try {
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5; // Simulate slower progress
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
                progressFill.setAttribute('aria-valuenow', progress);
            }
        }, 150); // Slower interval

        const response = await fetch('/api/submit', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval); // Stop simulation
        progressFill.style.width = '100%';
        progressFill.setAttribute('aria-valuenow', 100);

        if (response.ok) {
            const result = await response.json();
            showAlert('success', `✅ SUT soumis avec succès! ID: ${result.job_id.substring(0, 8)}`);

            setTimeout(() => {
                document.getElementById('uploadForm').reset();
                document.getElementById('fileName').style.display = 'none';
                progressBar.classList.add('d-none'); // Hide progress bar
                progressFill.style.width = '0%';
                progressFill.setAttribute('aria-valuenow', 0);
                loadJobs(); // Refresh immediately
                switchTab('jobs'); // Switch to jobs tab
            }, 1500); // Shorter delay
        } else {
            const error = await response.json();
            showAlert('error', `❌ Erreur: ${error.detail || 'Erreur inconnue'}`);
        }
    } catch (error) {
        showAlert('error', `❌ Erreur de connexion: ${error.message || 'Impossible de joindre le serveur'}`);
    } finally {
        submitBtn.disabled = false;
    }
}

async function loadJobs() {
    try {
        const response = await fetch('/api/jobs');
        const data = await response.json();

        console.log('Jobs loaded:', data); // Debug

        const statTotal = document.getElementById('statTotal');
        const statProcessing = document.getElementById('statProcessing');
        const statCompleted = document.getElementById('statCompleted');
        const statFailed = document.getElementById('statFailed');

        let processing = 0, completed = 0, failed = 0;

        if (data.jobs && Array.isArray(data.jobs)) {
            data.jobs.forEach(job => {
                const status = job.status || 'PENDING';
                // Consider jobs as completed if they have reached certain phases
                if (status === 'completed' || status === 'validated' || status === 'extracted' || status === 'reduced' || status === 'optimized') {
                    completed++;
                } else if (status === 'failed' || status === 'validation_failed' || status === 'extraction_failed' || status === 'reduction_failed' || status === 'optimization_failed' || status === 'execution_failed') {
                    failed++;
                } else {
                    processing++;
                }
            });
        }

        statTotal.textContent = data.total || 0;
        statProcessing.textContent = processing;
        statCompleted.textContent = completed;
        statFailed.textContent = failed;

        // Update metrics on Upload Section
        document.getElementById('totalJobs').textContent = data.total || 0;
        document.getElementById('completedJobs').textContent = completed;
        document.getElementById('successRate').textContent = data.total > 0 ? `${Math.round((completed / data.total) * 100)}%` : '0%';
        document.getElementById('avgReduction').textContent = data.avg_reduction ? `${Math.round(data.avg_reduction)}%` : '--';

        // Render jobs list
        const jobsListContainer = document.getElementById('jobsList');
        if (!jobsListContainer) return; // Ensure container exists

        if (!data.jobs || data.jobs.length === 0) {
            jobsListContainer.innerHTML = `
                <div class="text-center text-muted p-4">
                    <i class="bi bi-inbox fs-1"></i>
                    <p class="mt-2">Aucun emploi pour le moment.</p>
                </div>
            `;
        } else {
            jobsListContainer.innerHTML = data.jobs.map(job => {
                const status = job.status || 'PENDING';
                let statusClass = '';
                let iconClass = '';
                switch(status.toLowerCase()) {
                    case 'completed':
                    case 'validated':
                    case 'extracted':
                    case 'reduced':
                    case 'optimized': statusClass = 'bg-success'; iconClass = 'bi-check-circle-fill'; break;
                    case 'failed':
                    case 'validation_failed':
                    case 'extraction_failed':
                    case 'reduction_failed':
                    case 'optimization_failed':
                    case 'execution_failed': statusClass = 'bg-danger'; iconClass = 'bi-x-circle-fill'; break;
                    case 'validating':
                    case 'extracting':
                    case 'reducing':
                    case 'optimizing':
                    case 'executing':
                    case 'submitted':
                    case 'processing': statusClass = 'bg-warning'; iconClass = 'bi-hourglass-split'; break;
                    default: statusClass = 'bg-secondary'; iconClass = 'bi-question-circle-fill'; break;
                }

                // Format uploaded_at date
                const uploadedAt = job.uploaded_at ? new Date(job.uploaded_at).toLocaleString('fr-FR') : 'N/A';
                
                return `
                <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" onclick="viewJobDetails('${job.job_id}')">
                    <div class="d-flex flex-column text-start">
                        <h6 class="mb-1">📄 ${job.filename || `Job ${job.job_id.substring(0, 8)}`}</h6>
                        <small class="text-muted">ID: ${job.job_id}</small>
                        <small class="text-muted">Soumis le: ${uploadedAt}</small>
                    </div>
                    <span class="badge ${statusClass} rounded-pill fs-6 py-2 px-3">
                        <i class="bi ${iconClass} me-1"></i> ${status.toUpperCase()}
                    </span>
                </button>
            `;
            }).join('');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        showAlert('error', `❌ Erreur de chargement des emplois: ${error.message || 'Serveur inaccessible'}`);
    }
}

async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const services = await response.json();

        const servicesList = document.getElementById('servicesList');
        if (!servicesList) return; // Ensure container exists

        servicesList.innerHTML = Object.entries(services).map(([serviceKey, service]) => `
            <div class="col-md-4 col-lg-3">
                <div class="card h-100 shadow-sm">
                    <div class="card-body text-center">
                        <i class="bi ${
                            service.name.includes('Validator') ? 'bi-check-circle-fill' :
                            service.name.includes('Extractor') ? 'bi-box-arrow-up-right' :
                            service.name.includes('SGATS') ? 'bi-speedometer2' :
                            service.name.includes('EvoPath') ? 'bi-graph-up' :
                            service.name.includes('Executor') ? 'bi-play-circle-fill' : 'bi-gear-fill'
                        } fs-1 text-primary mb-3"></i>
                        <h5 class="card-title">${service.name}</h5>
                        <span class="badge ${service.status === 'online' ? 'bg-success' : 'bg-danger'} mb-2">
                            ${service.status.toUpperCase()}
                        </span>
                        <div class="btn-group btn-group-sm" role="group">
                            <button type="button" class="btn btn-outline-primary" onclick="checkServiceHealth('${serviceKey}')" title="Vérifier santé">
                                <i class="bi bi-heart-pulse"></i>
                            </button>
                            <button type="button" class="btn btn-outline-info" onclick="viewServiceLogs('${serviceKey}')" title="Voir logs">
                                <i class="bi bi-journal-text"></i>
                            </button>
                            <button type="button" class="btn btn-outline-warning" onclick="restartService('${serviceKey}')" title="Redémarrer">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading services:', error);
        showAlert('error', `❌ Erreur de chargement des services: ${error.message || 'Serveur inaccessible'}`);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('overviewTotal').textContent = stats.total_jobs;
        document.getElementById('overviewPassed').textContent = stats.completed;
        document.getElementById('overviewRate').textContent = `${Math.round(stats.success_rate)}%`;
        document.getElementById('overviewMutation').textContent = stats.mutation_score ? `${Math.round(stats.mutation_score)}%` : '--';
        document.getElementById('avgReduction').textContent = stats.mutation_score ? `${Math.round(stats.mutation_score)}%` : '--';

    } catch (error) {
        console.error('Error loading stats:', error);
        showAlert('error', `❌ Erreur de chargement des statistiques: ${error.message || 'Serveur inaccessible'}`);
    }
}

async function viewJobDetails(jobId) {
    // Fetch job details from API
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) {
            throw new Error(`Job ${jobId} not found`);
        }
        const job = await response.json();

        const modalTitle = document.getElementById('jobModalTitle');
        const modalContent = document.getElementById('jobModalContent');

        modalTitle.textContent = `Emploi: ${job.filename || jobId.substring(0, 8)}`;

        let phasesHTML = '';
        const phaseMapping = {
            'phase0': { name: 'Validation', icon: 'bi-check-circle' },
            'phase1': { name: 'Extraction', icon: 'bi-diagram-3' },
            'phase2': { name: 'Réduction SGATS', icon: 'bi-filter' },
            'phase3': { name: 'Optimisation EvoPath', icon: 'bi-graph-up' },
            'phase4': { name: 'Exécution & Mutation', icon: 'bi-play-circle' }
        };

        if (job.phases) {
            phasesHTML = `
                <h5 class="mt-4 mb-3">Phases d'exécution:</h5>
                <div class="row g-3">
                    ${Object.entries(phaseMapping).map(([phaseKey, phaseInfo]) => {
                        const phaseData = job.phases[phaseKey];
                        let status = 'pending';
                        let progress = 0;
                        let statusClass = 'border-secondary';
                        let badgeClass = 'bg-secondary';
                        let details = '';

                        if (phaseData) {
                            // Phase 0: Validation
                            if (phaseKey === 'phase0') {
                                status = job.status === 'validated' || job.status === 'completed' ? 'completed' : 'failed';
                                progress = 100;
                                statusClass = status === 'completed' ? 'border-success' : 'border-danger';
                                badgeClass = status === 'completed' ? 'bg-success' : 'bg-danger';
                                details = `
                                    <small class="text-muted d-block">Langage: ${phaseData.language || 'N/A'}</small>
                                    <small class="text-muted d-block">Fichiers: ${phaseData.files_count || 0}</small>
                                    <small class="text-muted d-block">Taille: ${(phaseData.size_bytes / 1024).toFixed(1)} KB</small>
                                `;
                            }
                            // Phase 1: Extraction
                            else if (phaseKey === 'phase1') {
                                status = job.trajectories_count ? 'completed' : 'pending';
                                progress = job.trajectories_count ? 100 : 0;
                                statusClass = job.trajectories_count ? 'border-success' : 'border-secondary';
                                badgeClass = job.trajectories_count ? 'bg-success' : 'bg-secondary';
                                if (job.trajectories_count) {
                                    details = `
                                        <small class="text-muted d-block">Trajectoires: ${job.trajectories_count}</small>
                                        <small class="text-muted d-block">Langage: ${phaseData.language || 'N/A'}</small>
                                    `;
                                }
                            }
                            // Phase 2: SGATS
                            else if (phaseKey === 'phase2' && job.sgats_stats) {
                                status = 'completed';
                                progress = 100;
                                statusClass = 'border-success';
                                badgeClass = 'bg-success';
                                const reduction = job.sgats_stats.reduction_rate || 0;
                                details = `
                                    <small class="text-muted d-block">Réduction: ${(reduction * 100).toFixed(1)}%</small>
                                    <small class="text-muted d-block">Initial: ${job.sgats_stats.initial_count || 0}</small>
                                    <small class="text-muted d-block">Final: ${job.sgats_stats.reduced_count || 0}</small>
                                `;
                            }
                            // Phase 3: EvoPath
                            else if (phaseKey === 'phase3' && job.evopath_stats) {
                                status = 'completed';
                                progress = 100;
                                statusClass = 'border-success';
                                badgeClass = 'bg-success';
                                const sizeRed = job.evopath_stats.size_reduction || 0;
                                const costRed = job.evopath_stats.cost_reduction || 0;
                                details = `
                                    <small class="text-muted d-block">Réduction taille: ${(sizeRed * 100).toFixed(1)}%</small>
                                    <small class="text-muted d-block">Réduction coût: ${(costRed * 100).toFixed(1)}%</small>
                                `;
                            }
                            // Phase 4: Execution & Mutation
                            else if (phaseKey === 'phase4' && job.execution_stats) {
                                status = 'completed';
                                progress = 100;
                                statusClass = 'border-success';
                                badgeClass = 'bg-success';
                                const passed = job.execution_stats.passed || 0;
                                const total = job.execution_stats.total || 0;
                                const mutationScore = job.mutation_stats ? job.mutation_stats.mutation_score : 0;
                                details = `
                                    <small class="text-muted d-block">Tests: ${passed}/${total} réussis</small>
                                    <small class="text-muted d-block">Mutation: ${mutationScore.toFixed(1)}%</small>
                                    <small class="text-muted d-block">Mutants tués: ${job.mutation_stats ? job.mutation_stats.killed : 0}/${job.mutation_stats ? job.mutation_stats.total_mutants : 0}</small>
                                `;
                            }
                        }

                        return `
                        <div class="col-md-6 col-lg-4">
                            <div class="card h-100 ${statusClass}">
                                <div class="card-body text-center p-3">
                                    <i class="bi ${phaseInfo.icon} fs-2 text-primary mb-2"></i>
                                    <h6 class="card-title text-primary">${phaseInfo.name}</h6>
                                    <div class="progress mb-2" style="height: 6px;">
                                        <div class="progress-bar bg-primary" role="progressbar" style="width: ${progress}%" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>
                                    </div>
                                    <span class="badge ${badgeClass} mb-2">
                                        ${status.charAt(0).toUpperCase() + status.slice(1)}
                                    </span>
                                    ${details}
                                </div>
                            </div>
                        </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        let additionalInfo = '';
        
        // Add mutation score if available
        if (job.mutation_stats && job.mutation_stats.mutation_score !== undefined) {
            additionalInfo += `<p><strong>Score de Mutation:</strong> ${job.mutation_stats.mutation_score.toFixed(1)}%</p>`;
        }
        
        // Add SGATS reduction info if available
        if (job.sgats_stats) {
            const reduction = job.sgats_stats.reduction_rate;
            if (reduction !== undefined) {
                additionalInfo += `<p><strong>Réduction SGATS:</strong> ${(reduction * 100).toFixed(1)}%</p>`;
            }
        }
        
        // Add EvoPath optimization info if available
        if (job.evopath_stats) {
            const sizeReduction = job.evopath_stats.size_reduction;
            const costReduction = job.evopath_stats.cost_reduction;
            if (sizeReduction !== undefined) {
                additionalInfo += `<p><strong>Réduction Taille (EvoPath):</strong> ${(sizeReduction * 100).toFixed(1)}%</p>`;
            }
            if (costReduction !== undefined) {
                additionalInfo += `<p><strong>Réduction Coût (EvoPath):</strong> ${(costReduction * 100).toFixed(1)}%</p>`;
            }
        }
        
        // Add execution stats if available
        if (job.execution_stats) {
            const passed = job.execution_stats.passed || 0;
            const total = job.execution_stats.total || 0;
            additionalInfo += `<p><strong>Tests Exécutés:</strong> ${passed}/${total} réussis</p>`;
        }
        
        // Add detailed error information
        if (job.error) {
            additionalInfo += `<div class="alert alert-danger mt-2"><strong>Erreur détaillée:</strong><br><code>${job.error}</code></div>`;
        }
        if (job.phase) {
            additionalInfo += `<p><strong>Échec à la phase:</strong> ${job.phase}</p>`;
        }

        modalContent.innerHTML = `
            <p><strong>ID:</strong> ${jobId}</p>
            <p><strong>Statut:</strong> <span class="badge ${getStatusBadgeClass(job.status)}">${job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1).toLowerCase() : 'N/A'}</span></p>
            <p><strong>Fichier:</strong> ${job.filename || 'N/A'}</p>                    <p><strong>Langage:</strong> ${job.sut_info ? job.sut_info.language : 'N/A'}${job.sut_info && job.sut_info.framework ? ` (${job.sut_info.framework})` : ''}</p>                    <p><strong>Taille:</strong> ${job.file_size ? (job.file_size / 1024).toFixed(1) + ' KB' : 'N/A'}</p>
            <p><strong>Soumis le:</strong> ${job.uploaded_at ? new Date(job.uploaded_at).toLocaleString('fr-FR') : 'N/A'}</p>
            ${additionalInfo}
            ${phasesHTML}
            ${job.trajectories && job.trajectories.length > 0 ? `
                <h5 class="mt-4 mb-3">Trajectoires de test extraites:</h5>
                <div class="accordion" id="trajectoriesAccordion">
                    ${job.trajectories.slice(0, 5).map((trajectory, index) => `
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="heading${index}">
                                <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}" aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse${index}">
                                    <strong>Trajectoire ${index + 1}</strong> - ${trajectory.method || 'Méthode inconnue'}
                                    <span class="badge bg-info ms-2">${trajectory.test_cases ? trajectory.test_cases.length : 0} cas de test</span>
                                </button>
                            </h2>
                            <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" aria-labelledby="heading${index}" data-bs-parent="#trajectoriesAccordion">
                                <div class="accordion-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <h6>Informations générales:</h6>
                                            <ul class="list-unstyled">
                                                <li><strong>Méthode:</strong> ${trajectory.method || 'N/A'}</li>
                                                <li><strong>Classe:</strong> ${trajectory.class || 'N/A'}</li>
                                                <li><strong>Fichier:</strong> ${trajectory.file || 'N/A'}</li>
                                                <li><strong>Ligne:</strong> ${trajectory.line || 'N/A'}</li>
                                                <li><strong>Complexité:</strong> ${trajectory.complexity || 'N/A'}</li>
                                            </ul>
                                        </div>
                                        <div class="col-md-6">
                                            <h6>Cas de test (${trajectory.test_cases ? trajectory.test_cases.length : 0}):</h6>
                                            ${trajectory.test_cases && trajectory.test_cases.length > 0 ? 
                                                `<div class="table-responsive">
                                                    <table class="table table-sm table-striped">
                                                        <thead>
                                                            <tr>
                                                                <th>Entrée</th>
                                                                <th>Sortie attendue</th>
                                                                <th>Type</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            ${trajectory.test_cases.slice(0, 3).map(tc => `
                                                                <tr>
                                                                    <td><code>${tc.input || 'N/A'}</code></td>
                                                                    <td><code>${tc.expected_output || 'N/A'}</code></td>
                                                                    <td><span class="badge bg-secondary">${tc.type || 'N/A'}</span></td>
                                                                </tr>
                                                            `).join('')}
                                                        </tbody>
                                                    </table>
                                                    ${trajectory.test_cases.length > 3 ? `<small class="text-muted">... et ${trajectory.test_cases.length - 3} autres cas de test</small>` : ''}
                                                </div>` : 
                                                '<p class="text-muted">Aucun cas de test généré</p>'
                                            }
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${job.trajectories.length > 5 ? `<p class="text-muted mt-2">... et ${job.trajectories.length - 5} autres trajectoires</p>` : ''}
            ` : ''}
            ${job.error ? `<div class="alert alert-danger mt-3"><strong>Erreur:</strong> ${job.error}</div>` : ''}
        `;

        jobDetailModal.show(); // Show modal using Bootstrap JS API
    } catch (error) {
        console.error('Error fetching job details:', error);
        showAlert('error', `❌ Erreur de chargement des détails de l'emploi: ${error.message || 'Détails non trouvés'}`);
    }
}

// Helper for status badge classes
function getStatusBadgeClass(status) {
    switch(status ? status.toLowerCase() : 'n/a') {
        case 'completed':
        case 'validated':
        case 'extracted':
        case 'reduced':
        case 'optimized': return 'bg-success';
        case 'failed':
        case 'validation_failed':
        case 'extraction_failed':
        case 'reduction_failed':
        case 'optimization_failed':
        case 'execution_failed': return 'bg-danger';
        case 'validating':
        case 'extracting':
        case 'reducing':
        case 'optimizing':
        case 'executing':
        case 'submitted':
        case 'processing': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

// Close modal is handled by Bootstrap's data-bs-dismiss="modal"
// function closeJobModal() {
//     jobDetailModal.hide();
// }

// Service management functions
async function checkServiceHealth(serviceKey) {
    showAlert('info', `🔍 Vérification de la santé du service ${serviceKey}...`);
    try {
        const response = await fetch(`/api/services/${serviceKey}/health`);
        if (response.ok) {
            const health = await response.json();
            showAlert('success', `✅ Service ${serviceKey} est sain: ${JSON.stringify(health)}`);
        } else {
            showAlert('error', `❌ Service ${serviceKey} n'est pas accessible`);
        }
    } catch (error) {
        showAlert('error', `❌ Erreur de vérification: ${error.message}`);
    }
}

async function viewServiceLogs(serviceKey) {
    showAlert('info', `📋 Récupération des logs du service ${serviceKey}...`);
    try {
        const response = await fetch(`/api/services/${serviceKey}/logs`);
        if (response.ok) {
            const logs = await response.text();
            // Show logs in a modal or alert
            const logsModal = new bootstrap.Modal(document.getElementById('jobModal'));
            document.getElementById('jobModalTitle').textContent = `Logs du service ${serviceKey}`;
            document.getElementById('jobModalContent').innerHTML = `<pre style="max-height: 400px; overflow-y: auto;">${logs}</pre>`;
            logsModal.show();
        } else {
            showAlert('error', `❌ Impossible de récupérer les logs du service ${serviceKey}`);
        }
    } catch (error) {
        showAlert('error', `❌ Erreur de récupération des logs: ${error.message}`);
    }
}

async function restartService(serviceKey) {
    if (!confirm(`Êtes-vous sûr de vouloir redémarrer le service ${serviceKey} ?`)) {
        return;
    }
    showAlert('warning', `🔄 Redémarrage du service ${serviceKey}...`);
    try {
        const response = await fetch(`/api/services/${serviceKey}/restart`, { method: 'POST' });
        if (response.ok) {
            showAlert('success', `✅ Service ${serviceKey} redémarré avec succès`);
            loadServices(); // Refresh services status
        } else {
            showAlert('error', `❌ Échec du redémarrage du service ${serviceKey}`);
        }
    } catch (error) {
        showAlert('error', `❌ Erreur de redémarrage: ${error.message}`);
    }
}

function switchTab(tabId) {
    document.querySelectorAll('div[id$="Section"]').forEach(el => {
        el.style.display = 'none';
    });
    const targetSection = document.getElementById(tabId + 'Section');
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    window.history.pushState({}, '', `#${tabId}`);
    // Update active state for nav links
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.classList.remove('active');
    });
    const activeLink = document.querySelector(`.navbar-nav a[onclick*="switchTab('${tabId}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    return false;
}

// This function becomes simpler with Bootstrap tabs
function switchStatsTab(tabId) {
    // Bootstrap handles tab switching itself via data-bs-toggle="tab"
    // We just need to ensure the correct tab content is shown if it's not handled by Bootstrap's default
    const targetTabPane = document.getElementById(tabId + 'Tab');
    if (targetTabPane) {
        const bsTab = new bootstrap.Tab(targetTabPane);
        bsTab.show();
    }
    return false; // Prevent default button behavior
}
