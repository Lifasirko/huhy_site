document.addEventListener('DOMContentLoaded', () => {
    const selectors = {
        calendarEvents: 'calendar-events',
        eventsUrl: 'events-url',
        prevBtn: 'prev-btn',
        nextBtn: 'next-btn',
    };

    let currentPage = 1;
    const eventsPerPage = 3;
    let allEvents = [];

    const elements = {};
    Object.keys(selectors).forEach(key => {
        const selector = selectors[key];
        elements[key] = document.getElementById(selector) || document.querySelector(selector);
    });

    function fetchEvents() {
        fetch(`${elements.eventsUrl.dataset.url}?page=${currentPage}&limit=${eventsPerPage}`)
            .then(response => response.json())
            .then(data => {
                allEvents = data.events;
                renderEvents();
                updateButtonStates(data.has_more);
            })
            .catch(error => console.error('Error fetching events:', error));
    }

    function renderEvents() {
        const carouselContainer = elements.calendarEvents;
        carouselContainer.innerHTML = '';
        allEvents.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.innerHTML = `
                <div class="event-card-content">
                    <h3><span>${event.summary}</span></h3>
                    <p>Початок: ${new Date(event.start).toLocaleString()}</p>
                    <p>Кінець: ${new Date(event.end).toLocaleString()}</p>
                    <p>${event.description || 'Опис відсутній'}</p>
                </div>
                <div class="button-container">
                    <a href="https://t.me/hyhu_space" class="sign-up">Записатись</a>
                </div>
            `;
            carouselContainer.appendChild(eventCard);
        });
    }

    function updateButtonStates(hasMore) {
        elements.prevBtn.disabled = currentPage === 1;
        elements.nextBtn.disabled = !hasMore;
    }

    elements.prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            fetchEvents();
        }
    });

    elements.nextBtn.addEventListener('click', () => {
        currentPage++;
        fetchEvents();
    });

    fetchEvents();
});
