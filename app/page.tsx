"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles } from "lucide-react";

export default function NaturalLanguageGenerator() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { id: 1, role: "system", content: "Welcome! How can I assist you today?" },
    {
      id: 2,
      role: "user",
      content: "Can you explain what a natural language generator does?",
    },
    {
      id: 3,
      role: "system",
      content:
        "A natural language generator is an AI-powered system that produces human-like text based on input or prompts. It can be used for various purposes such as content creation, chatbots, or automated reporting.",
    },
  ]);

  const connectWebSocket = useCallback(() => {
    websocket.current = new WebSocket("ws://localhost:8000/ws");
  
    websocket.current.onopen = () => {
      console.log("WebSocket connection opened");
    };
  
    websocket.current.onmessage = (event) => {
      console.log("Message received from backend:", event.data);
      setMessages((prev) => [
        ...prev,
        { id: prev.length + 1, role: "system", content: event.data },
      ]);
    };
  
    websocket.current.onclose = () => {
      console.log("WebSocket connection closed");
      setTimeout(connectWebSocket, 1000);
    };
  }, []);
  
  const websocket = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
  
    return () => {
      if (websocket.current) {
        websocket.current.close();
      }
    };
  }, [connectWebSocket]); // No dependencies to avoid unnecessary re-runs


  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (
      input.trim() &&
      websocket.current &&
      websocket.current.readyState === WebSocket.OPEN
    ) {
      const message = { id: messages.length + 1, role: "user", content: input };
      setMessages((prev) => [...prev, message]);
      websocket.current.send(input);
      setInput("");
    } else {
      console.log("WebSocket is not open");
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="bg-light-blue-50 p-4 shadow-sm">
        <h1 className="text-2xl font-bold text-light-blue-800 flex items-center justify-center">
          <Sparkles className="w-6 h-6 mr-2 text-light-blue-500" />
          Natural Language Generator
        </h1>
      </header>

      <main className="flex-grow overflow-auto p-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${
                m.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  m.role === "user"
                    ? "bg-light-blue-100 text-light-blue-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
        </div>
      </main>

      <footer className="bg-light-blue-50 p-4 shadow-lg">
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto flex space-x-2"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your prompt here..."
            className="flex-grow border-light-blue-300 focus:ring-light-blue-500 focus:border-light-blue-500"
          />
          <Button
            type="submit"
            className="bg-light-blue-500 hover:bg-light-blue-600 text-white"
          >
            Generate
          </Button>
        </form>
      </footer>
    </div>
  );
}
