import { useEffect, useState } from "react";
import "./App.css";

type HelloResponse = {
    message: string;
};

function App() {
    const [hello, setHello] = useState("");

    useEffect(() => {
        fetch("/api/hello")
            .then((res) => res.json())
            .then((data: HelloResponse) => {
                setHello(data.message);
            });
    }, []);

    return <h1>{hello}</h1>;
}

export default App;
