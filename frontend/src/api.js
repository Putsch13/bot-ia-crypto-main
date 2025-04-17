import axios from "axios";


const API_URL = "http://127.0.0.1:5002";

export const getSentimentReport = async () => {
  const res = await axios.get(`${API_URL}/analyser_sentiment`);
  return res.data;
};
export async function startBot(params) {
  const res = await fetch("http://localhost:5002/start_bot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  })
  return await res.json()
}