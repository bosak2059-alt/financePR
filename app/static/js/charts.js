/**
 * Finance Tracker - Chart Configuration
 * Библиотека: Chart.js
 */

// Глобальные настройки для всех графиков
Chart.defaults.font.family = "'Segoe UI', 'Helvetica', 'Arial', sans-serif";
Chart.defaults.color = '#858796';

/**
 * Построение круговой диаграммы расходов по категориям
 * @param {string} canvasId - ID элемента canvas
 * @param {array} labels - Названия категорий
 * @param {array} data - Значения сумм
 */
function createCategoryChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx || data.length === 0) {
        console.log('Нет данных для графика категорий');
        return;
    }
    
    const colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', 
        '#e74a3b', '#858796', '#5a5c69', '#6610f2'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, data.length),
                hoverBackgroundColor: colors.slice(0, data.length),
                hoverBorderColor: 'rgba(234, 236, 244, 1)',
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                    }
                },
                tooltip: {
                    backgroundColor: 'rgb(255,255,255)',
                    bodyColor: '#858796',
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    titleColor: '#4e73df',
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.parsed || 0;
                            return `${label}: ${value.toLocaleString('ru-RU')} ₽`;
                        }
                    }
                }
            },
            cutout: '70%',
        }
    });
}

/**
 * Построение линейного графика динамики доходов/расходов
 * @param {string} canvasId - ID элемента canvas
 * @param {array} labels - Месяцы
 * @param {array} incomeData - Данные доходов
 * @param {array} expenseData - Данные расходов
 */
function createTrendChart(canvasId, labels, incomeData, expenseData) {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx || labels.length === 0) {
        console.log('Нет данных для графика трендов');
        return;
    }
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Доходы',
                    data: incomeData,
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Расходы',
                    data: expenseData,
                    borderColor: '#e74a3b',
                    backgroundColor: 'rgba(231, 74, 59, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ],
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    backgroundColor: 'rgb(255,255,255)',
                    bodyColor: '#858796',
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    titleColor: '#4e73df',
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            let value = context.parsed.y || 0;
                            return `${label}: ${value.toLocaleString('ru-RU')} ₽`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        borderDash: [2],
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index',
            },
        }
    });
}

/**
 * Построение столбчатой диаграммы (сравнение по месяцам)
 * @param {string} canvasId - ID элемента canvas
 * @param {array} labels - Месяцы
 * @param {array} data - Значения
 * @param {string} label - Название набора данных
 */
function createBarChart(canvasId, labels, data, label = 'Значения') {
    const ctx = document.getElementById(canvasId);
    
    if (!ctx || data.length === 0) {
        return;
    }
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: '#4e73df',
                borderColor: '#4e73df',
                borderRadius: 5,
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('ru-RU') + ' ₽';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Инициализация всех графиков на странице
 * Вызывается после загрузки DOM
 */
function initCharts() {
    // Проверка наличия элементов перед инициализацией
    const categoryCanvas = document.getElementById('categoryChart');
    const trendCanvas = document.getElementById('trendChart');
    
    if (categoryCanvas && window.categoryLabels && window.categoryData) {
        createCategoryChart('categoryChart', window.categoryLabels, window.categoryData);
    }
    
    if (trendCanvas && window.trendLabels && window.trendIncome && window.trendExpense) {
        createTrendChart('trendChart', window.trendLabels, window.trendIncome, window.trendExpense);
    }
}

// Автозапуск после загрузки страницы
document.addEventListener('DOMContentLoaded', initCharts);