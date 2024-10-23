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

    function parseEventDescription(description) {
        // Регулярні вирази для витягування полів
        const gameRegex = /Майстер\s(.+)\s\((.+)\)/;  // Витягуємо майстра та назву гри
        const freeSeatsRegex = /Вільні місця:\s(\d+)/;  // Витягуємо вільні місця
        const costRegex = /Вартість:\s(\d+)/;  // Витягуємо вартість

        const gameMatch = description.match(gameRegex);
        const freeSeatsMatch = description.match(freeSeatsRegex);
        const costMatch = description.match(costRegex);

        // Парсинг результатів
        const master = gameMatch ? gameMatch[1] : 'Невідомо';
        const game = gameMatch ? gameMatch[2] : 'Невідомо';
        const freeSeats = freeSeatsMatch ? freeSeatsMatch[1] : 'Невідомо';
        const cost = costMatch ? costMatch[1] : 'Невідомо';

        return {
            game,
            master,
            freeSeats,
            cost,
            remainingDescription: description.split("Щоб записатись")[0].trim(),  // Обрізаємо все, що після вказівки як записатися
        };
    }

    function renderEvents() {
        const carouselContainer = elements.calendarEvents;
        carouselContainer.innerHTML = '';
        allEvents.forEach(event => {
            const startDateTime = new Date(event.start);
            const endDateTime = new Date(event.end);

            // Форматуємо дату та час
            const formattedDate = `${startDateTime.getDate().toString().padStart(2, '0')}-${(startDateTime.getMonth() + 1).toString().padStart(2, '0')}-${startDateTime.getFullYear()}`;
            const formattedTime = `${startDateTime.getHours().toString().padStart(2, '0')}:${startDateTime.getMinutes().toString().padStart(2, '0')} — ${endDateTime.getHours().toString().padStart(2, '0')}:${endDateTime.getMinutes().toString().padStart(2, '0')}`;

            // Парсинг опису
            const parsedDescription = parseEventDescription(event.description || '');

            // Створюємо картку події
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.innerHTML = `
                <div class="event-card-content">
                    <h3><span>${event.summary}</span></h3>
                    <ul>
                        <li><strong>Гра:</strong> ${parsedDescription.game}</li>
                        <li><strong>Дата:</strong> ${formattedDate}</li>
                        <li><strong>Час:</strong> ${formattedTime}</li>
                        <li><strong>Майстер:</strong> ${parsedDescription.master}</li>
                        <li><strong>Всього гравців:</strong> 5</li>
                        <li><strong>Вільні місця:</strong> ${parsedDescription.freeSeats}</li>
                        <li><strong>Вартість:</strong> ${parsedDescription.cost} грн з гравця</li>
                    </ul>
                    <p>${parsedDescription.remainingDescription}</p>
                    <p>Щоб записатись на гру пишіть на наш телеграм <a href="https://t.me/hyhu_space">@hyhu_space</a></p>
                </div>
                <div class="telegram-button-container">
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
