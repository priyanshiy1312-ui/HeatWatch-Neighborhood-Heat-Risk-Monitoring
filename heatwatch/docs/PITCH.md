# HeatWatch pitch kit

## One line
HeatWatch tells a city which neighbourhoods will suffer most in tomorrow's heat and water shortage, what to do about it, and warns residents in Hindi.

## 2-3 minute demo script
1. (0:00) Problem: city-wide heat alerts hide that dense areas like the Walled City run far hotter than leafy ones like C-Scheme, and these are the areas with the least water.
2. (0:20) Open the map on Today. Point out the colour bands, then switch to Day 3 and show wards turning red.
3. (0:50) Officer view: the top-5 list says where to act first.
4. (1:05) Click the top ward. Show the score bars: heat risk and water stress, and why.
5. (1:30) "What to do": cooling shelter, tanker, stop outdoor work 12 to 4.
6. (1:50) Switch the advisory to Hindi (written by Amazon Bedrock). Press "Send alert" and show the email arriving via SNS.
7. (2:20) Architecture slide: Lambda, API Gateway, Bedrock, SNS, DynamoDB, EventBridge. Close with the scale-up path.

## Likely judge questions
- Is the data real? Forecast is live from Open-Meteo. Ward values are labelled sample proxies, and the pipeline accepts census, WorldPop and MODIS data.
- Why not just a dashboard? It recommends actions and sends alerts automatically every 3 hours.
- How does it scale? Add city ward GeoJSON and data files. Nothing else changes.
- What if Bedrock or the network fails? Template advisories and a sample forecast keep the demo working, clearly labelled.

## Future scope
Real ward boundaries and census data, MODIS land temperature, WhatsApp alerts, flood and drought layers, sensor-based tank levels, feedback from field workers.
