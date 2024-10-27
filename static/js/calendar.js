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

    function parseEventDescription(summary, description) {
        // Регулярні вирази для витягування полів
        const summaryRegex = /^(.+?)(?:\s*[.-]\s*(?:Кімната\s.*\s)?)?[Мм]айстер\s(.+)$/;  // Витягуємо майстра та назву гри
        const freeSeatsRegex = /Вільні місця:\s(\d+)/;  // Витягуємо вільні місця
        const costRegex = /Вартість:\s(\d+)/;  // Витягуємо вартість

        const gameMatch = summary.match(summaryRegex);
        const freeSeatsMatch = description.match(freeSeatsRegex);
        const costMatch = description.match(costRegex);

        // Парсинг результатів
        const master = gameMatch ? gameMatch[2] : '—';
        const game = gameMatch ? gameMatch[1] : 'Вільна кімната';
        const freeSeats = freeSeatsMatch ? freeSeatsMatch[1] : '—';
        const cost = costMatch ? costMatch[1] : '—';

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
            const formattedTime = `${startDateTime.getHours().toString().padStart(2, '0')}:${startDateTime.getMinutes().toString().padStart(2, '0')}`;

            // Парсинг опису
            const parsedDescription = parseEventDescription(event.summary, event.description || '');


            // Default image path
            const defaultImage = "../static/images/calendar_pics/slay.png"; // Path to the default image
            const images = {
                'підземелля': "../static/images/calendar_pics/dd.png", // Path for Підземелля та дракони
                'підземелля': "../static/images/calendar_pics/dd.png",
                'підземелля': "../static/images/calendar_pics/dd.png",
                'star': "../static/images/calendar_pics/sw.jpg",
                'вільна': "../static/images/calendar_pics/free_chamber.png",
                // Add more games and their image paths here
            };

            // Визначаємо фото гри
            let gameImage = defaultImage; // Start with the default image
            for (const key in images) {
                if (parsedDescription.game.toLowerCase().includes(key)) {
                    gameImage = images[key]; // Set the specific image if game name matches
                    break; // Stop searching after finding the first match
                }
            }

            console.log('Game Name:', parsedDescription.game); // Debugging
            console.log('Image Path:', gameImage);




            // Створюємо картку події
            const eventCard = document.createElement('div');
            eventCard.className = 'event-card';
            eventCard.innerHTML = `
                <img class="calendar-imgs" src="${gameImage}" alt="${parsedDescription.game}" class="event-image">
                <div class="event-card-content">
                    <h3><span>${event.summary}</span></h3>
                    <span class="game-name">${parsedDescription.game}</span>

                    <div class="master-div">
                        <img class="calendar-icon" src="../static/images/calendar_icons/school.png">
                        <span class="span-for-icons">Майстер: ${parsedDescription.master}</span>
                    </div>

                    <span><strong>Гра:</strong> ${parsedDescription.game}</span>
                    <span><strong>Дата:</strong> ${formattedDate}</span>
                    <span><strong>Час:</strong> ${formattedTime}</span>

                    <span><strong>Вільні місця:</strong> ${parsedDescription.freeSeats}</span>
                    <span><strong>Вартість:</strong> ${parsedDescription.cost} грн з гравця</span>

                    <p>${parsedDescription.remainingDescription}</p>
                    <p>Щоб записатись на гру пишіть на наш телеграм @hyhu_space</a></p>
                </div>
                <div class="telegram-button-container">
                    <a href="https://t.me/hyhu_space" class="sign-up" target="_blank">Записатись на гру</a>
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
