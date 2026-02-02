
const SERVICE_URL = "https://ufc-predictions-685306641609.us-central1.run.app";

export const getRoot = async () => {
  try {
    const response = await fetch(`${SERVICE_URL}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to fetch root");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching root:", error);
    return null;
  }
};

export const getPredictions = async (fighter1, fighter2) => {
  const fighterTag1 = fighter1
  .toLowerCase()
  .replace(/-/g, " ")
  .split(/\s+/)
  .join("_");

  const fighterTag2 = fighter2
  .toLowerCase()
  .replace(/-/g, " ")
  .split(/\s+/)
  .join("_");

  console.log(fighterTag1, fighterTag2);

  try {
    const response = await fetch(`${SERVICE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        red_fighter: fighterTag1,
        blue_fighter: fighterTag2,
      }),
    });
    console.log(response);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Prediction failed");
    }

    const data = await response.json();
    console.log("Prediction:", data);
    return data;
  } catch (error) {
    console.error("Error fetching prediction:", error);
    return null;
  }
};

export const getUpcoming = async () => {
  try {
    const response = await fetch(`${SERVICE_URL}/upcoming`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to fetch upcoming fights");
    }

    const data = await response.json();
    return data.fights || [];
  } catch (error) {
    console.error("Error fetching upcoming fights:", error);
    return [];
  }
};

export const getPrevious = async () => {
  try {
    const response = await fetch(`${SERVICE_URL}/previous`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to fetch previous fights");
    }

    const data = await response.json();
    return data.fights || [];
  } catch (error) {
    console.error("Error fetching previous fights:", error);
    return [];
  }
};