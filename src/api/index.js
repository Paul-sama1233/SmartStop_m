import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

export default {
  // Маршруты
  getRoutes() {
    return api.get('/routes/')
  },
  getRouteByNumber(number) {
  return api.get(`/routes/by-number/${number}/`)
  },
  getActiveStops() {
  return api.get('/active-stops/')
},
  getNearbyStops(lat, lng, radius = 150) {
  return api.get('/nearby-stops/', { params: { lat, lng, radius } })
},

  // Транспорт на карте
  getVehiclesOnMap() {
    return api.get('/vehicles/on-map/')
  },

  // Метро
  getMetroLines() {
    return api.get('/metro/lines/')
  },
  getMetroStations() {
    return api.get('/metro/stations/')
  },
  getJourney(fromLat, fromLng, toLat, toLng) {
  return api.get('/journey/', {
    params: { from_lat: fromLat, from_lng: fromLng, to_lat: toLat, to_lng: toLng }
  })
},

  // Табло
  getBoard() {
    return api.get('/board/')
  }
}
