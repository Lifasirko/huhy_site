document.addEventListener('DOMContentLoaded', () => {
    const selectors = {
        prevMonthBtn: 'prev-month',
        nextMonthBtn: 'next-month',
        todayBtn: 'today',
        currentMonthSpan: 'current-month',
        eventList: 'event-list',
        showMoreBtn: 'show-more-btn',
        eventsUrl: 'events-url',
        showPastEventsBtn: 'show-past-events',
        eventPopup: 'event-popup',
        overlay: 'overlay',
        popupEventTitle: 'popup-event-title',
        popupEventTime: 'popup-event-time',
        popupEventDescription: 'popup-event-description',
        closePopupBtn: '.close-popup'
    };

    const elements = {};
    Object.keys(selectors).forEach(key => {
        const selector = selectors[key];
        elements[key] = document.getElementById(selector) || document.querySelector(selector);
    });

    const monthNames = [
        "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", 
        "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"
    ];
    const weekdays = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

    let currentDate = new Date();
    let allDayBlocks = [];
    const VISIBLE_DAYS = 15;

    const formatDate = dateString => {
        const date = new Date(dateString);
        return `${weekdays[date.getDay()]}<br>${date.getDate()}`;
    };

    const formatTime = timeString => timeString.split('T')[1].substring(0, 5);

    const groupEventsByDate = events => events.reduce((acc, event) => {
        const date = event.start.split('T')[0];
        acc[date] = acc[date] || [];
        acc[date].push(event);
        return acc;
    }, {});

    const showEventPopup = event => {
        elements.popupEventTitle.textContent = event.summary;
        elements.popupEventTime.textContent = `${formatTime(event.start)} - ${formatTime(event.end)}`;
        elements.popupEventDescription.textContent = event.description || 'Опис відсутній';
        elements.eventPopup.style.display = 'block';
        elements.overlay.style.display = 'block';
    };

    const closeEventPopup = () => {
        elements.eventPopup.style.display = 'none';
        elements.overlay.style.display = 'none';
    };

    const updateCalendar = date => {
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
    
        elements.currentMonthSpan.textContent = `${monthNames[date.getMonth()]} ${year}`;
        elements.eventList.innerHTML = '';
    
        try {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', `${elements.eventsUrl.dataset.url}?year=${year}&month=${month}`, false); // false makes it synchronous
            xhr.send();
    
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
    
                if (data.events?.length > 0) {
                    const today = new Date().toISOString().split('T')[0];
                    const currentYear = new Date().getFullYear();
                    const currentMonth = new Date().getMonth() + 1;
                    const eventsByDate = groupEventsByDate(data.events);

                    let visibleDays = 0;
                    let hasPastEvents = false;
    
                    allDayBlocks = [];
    
                    Object.entries(eventsByDate).forEach(([date, events]) => {
                        const dayBlock = document.createElement('div');
                        dayBlock.className = `day-block ${date === today ? 'current-day' : ''} ${date < today && currentMonth == month && currentYear == year ? 'past-events' : ''}`;
                        
                        if (date < today && currentMonth == month && currentYear == year) hasPastEvents = true;
    
                        dayBlock.innerHTML = `
                            <div class="day-date">${formatDate(date)}</div>
                            <div class="day-events">
                                ${events.map(event => `
                                    <div class="event-item">
                                        <div class="event-title">${event.summary}</div>
                                        <div class="event-time">${formatTime(event.start)} - ${formatTime(event.end)}</div>
                                    </div>
                                `).join('')}
                            </div>
                        `;
    
                        dayBlock.querySelectorAll('.event-item').forEach((item, index) => {
                            item.addEventListener('click', () => showEventPopup(events[index]));
                        });
    
                        if (visibleDays < VISIBLE_DAYS) {
                            elements.eventList.appendChild(dayBlock);
                        } else {
                            dayBlock.style.display = 'none';
                            allDayBlocks.push(dayBlock);
                        }
    
                        visibleDays++;
                    });

                    elements.showMoreBtn.textContent = allDayBlocks.length > 0 ? 'Показати ще' : '';
                    elements.showMoreBtn.style.display = allDayBlocks.length > 0 ? 'block' : 'none';
    
                    if (hasPastEvents) {
                        elements.showPastEventsBtn.style.display = 'inline-block';
                        elements.showPastEventsBtn.textContent = 'Показати минулі події';
                        elements.showPastEventsBtn.onclick = () => {
                            const pastEvents = document.querySelectorAll('.past-events');
                            pastEvents.forEach(event => event.style.display = 'flex');
                            elements.showPastEventsBtn.textContent = '';
                        };
                    } else {
                        elements.showPastEventsBtn.style.display = 'none';
                    }
    
                } else {
                    elements.eventList.innerHTML = '<p>Немає подій</p>';
                    elements.showPastEventsBtn.style.display = 'none';
                    elements.showMoreBtn.style.display = 'none'
                }
            } else {
                elements.eventList.innerHTML = '<p>Помилка завантаження подій</p>';
                elements.showPastEventsBtn.style.display = 'none';
                elements.showMoreBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Error:', error);
            elements.eventList.innerHTML = '<p>Помилка завантаження подій</p>';
            elements.showPastEventsBtn.style.display = 'none';
            elements.showMoreBtn.style.display = 'none';
        }
    };
    
    elements.closePopupBtn.addEventListener('click', closeEventPopup);
    elements.overlay.addEventListener('click', closeEventPopup);

    elements.prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        updateCalendar(currentDate);
    });

    elements.nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        updateCalendar(currentDate);
    });

    elements.todayBtn.addEventListener('click', () => {
        currentDate = new Date();
        updateCalendar(currentDate);
    });

    elements.showMoreBtn.addEventListener('click', () => {
        allDayBlocks.splice(0, VISIBLE_DAYS).forEach(dayBlock => {
            dayBlock.style.display = 'flex';
            elements.eventList.appendChild(dayBlock);
        });
        if (!allDayBlocks.length) elements.showMoreBtn.style.display = 'none';
    });

    updateCalendar(currentDate);
});
