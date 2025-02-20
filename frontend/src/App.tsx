import { useEffect, useState } from "react";
import "./App.css";

type HelloResponse = {
    message: string;
};

function App() {
    const [hello, setHello] = useState("");
    const [statusMessage, setStatusMessage] = useState("");
    const [userData, setUserData] = useState("");

    useEffect(() => {
        fetch("/api/get-test-user")
            .then((res) => res.json())
            .then((data: HelloResponse) => {
                setHello(JSON.stringify(data));
            });
    }, []);

    return (
        <div>
            <h1>{hello}</h1>
            <form
                onSubmit={(e) => {
                    // send form data to the server
                    e.preventDefault();
                    const formData = new FormData(e.target as HTMLFormElement);
                    const data = {
                        spotify_id: formData.get("spotify_id") as string,
                        access_token: formData.get("access_token") as string,
                        refresh_token: formData.get("refresh_token") as string,
                        token_expires_at: formData.get(
                            "token_expires_at"
                        ) as string,
                        last_synced_at: formData.get(
                            "last_synced_at"
                        ) as string,
                        is_active:
                            (formData.get("is_active") as string) === "on",
                    };

                    fetch("/api/add-spotify-user", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(data),
                    })
                        .then((res) => res.json())
                        .then((data) => {
                            setStatusMessage(JSON.stringify(data));
                        });
                }}
            >
                <div>
                    <label htmlFor='spotify_id'>Spotify ID:</label>
                    <input
                        type='text'
                        id='spotify_id'
                        name='spotify_id'
                        required
                    />
                </div>
                <div>
                    <label htmlFor='access_token'>Access Token:</label>
                    <input
                        type='text'
                        id='access_token'
                        name='access_token'
                        required
                    />
                </div>
                <div>
                    <label htmlFor='refresh_token'>Refresh Token:</label>
                    <input
                        type='text'
                        id='refresh_token'
                        name='refresh_token'
                        required
                    />
                </div>
                <div>
                    <label htmlFor='token_expires_at'>Token Expires At:</label>
                    <input
                        type='date'
                        id='token_expires_at'
                        name='token_expires_at'
                        required
                    />
                </div>
                <div>
                    <label htmlFor='last_synced_at'>Last Synced At:</label>
                    <input
                        type='date'
                        id='last_synced_at'
                        name='last_synced_at'
                    />
                </div>
                <div>
                    <label htmlFor='is_active'>Is Active:</label>
                    <input type='checkbox' id='is_active' name='is_active' />
                </div>
                <button type='submit'>Submit</button>
            </form>
            <pre>{statusMessage}</pre>
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target as HTMLFormElement);
                    const spotify_id = formData.get("spotify_id") as string;
                    fetch(`/api/get-spotify-user?spotify_id=${spotify_id}`)
                        .then((res) => res.json())
                        .then((data) => {
                            setUserData(JSON.stringify(data, null, 2));
                        });
                }}
            >
                <div>
                    <label htmlFor='spotify_id'>Spotify ID:</label>
                    <input
                        type='text'
                        id='spotify_id'
                        name='spotify_id'
                        required
                    />
                </div>
                <button type='submit'>Get User</button>
                <pre>{userData}</pre>
            </form>
        </div>
    );
}

export default App;
