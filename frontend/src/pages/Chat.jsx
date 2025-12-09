import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { promptAPI, conversationAPI } from "../utils/api";
import Button from "../components/Button";
import LoadingSpinner from "../components/LoadingSpinner";
import Sidebar from "../components/Sidebar";

const Chat = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoadingConversations(true);
      const data = await conversationAPI.getConversations();
      setConversations(data.conversations || []);
    } catch (error) {
      console.error("Error loading conversations:", error);
    } finally {
      setLoadingConversations(false);
    }
  };

  const loadConversation = async (conversationId) => {
    try {
      setLoading(true);
      const data = await conversationAPI.getConversation(conversationId);
      setMessages(data.messages || []);
      setCurrentConversationId(conversationId);
      setSidebarOpen(false); // Close sidebar on mobile after selection
    } catch (error) {
      console.error("Error loading conversation:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
    setSidebarOpen(false);
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      await conversationAPI.deleteConversation(conversationId);
      setConversations(conversations.filter((c) => c.id !== conversationId));
      
      // If we deleted the current conversation, start a new one
      if (conversationId === currentConversationId) {
        handleNewConversation();
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
      throw error;
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!inputValue.trim() || loading) {
      return;
    }

    const userMessage = inputValue.trim();
    setInputValue("");

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage, timestamp: new Date() },
    ]);

    setLoading(true);

    try {
      const response = await promptAPI.sendPrompt(userMessage, currentConversationId);

      console.log(`response:`, response);

      // Update conversation ID if this is a new conversation
      if (response.conversation_id && !currentConversationId) {
        setCurrentConversationId(response.conversation_id);
        // Reload conversations to show the new one
        loadConversations();
      }

      // Add AI response to chat
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.response || "Response received from API",
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error("Error sending prompt:", error);
      
      // Extract the error message from the backend response
      let errorMessage = "Sorry, there was an error processing your request. Please try again.";
      
      if (error.response?.data?.error) {
        // Backend returned a specific error message
        errorMessage = error.response.data.error;
      } else if (error.message) {
        // Use the error message if available
        errorMessage = error.message;
      }
      
      // Add error message to chat
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: errorMessage,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={loadConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile menu button */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="text-xl font-bold text-gray-900">MediWise.AI</h1>
          </div>
          <Button onClick={handleLogout} variant="outline" className="text-sm">
            Logout
          </Button>
        </header>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="inline-block p-4 bg-blue-100 rounded-full mb-4">
                  <svg
                    className="w-12 h-12 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Welcome to MediWise.AI
                </h2>
                <p className="text-gray-600 max-w-md mx-auto">
                  Ask me anything about medications, side effects, dosages, and
                  more. I'm here to help you understand your medicines better.
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : message.role === "error"
                        ? "bg-red-50 text-red-900 border border-red-200"
                        : "bg-white text-gray-900 border border-gray-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))
            )}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <LoadingSpinner size="sm" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white px-4 py-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter medication name (e.g., Xarelto)"
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="1"
                  style={{
                    minHeight: "52px",
                    maxHeight: "200px",
                  }}
                  disabled={loading}
                />
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={!inputValue.trim() || loading}
                className="px-6 py-3 h-[52px]"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send, Shift + Enter for new line
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
