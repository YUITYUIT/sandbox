import React, { useState } from "react";
import BookList from "./components/BookList";

function App() {
  const [books, setBooks] = useState([]);
  const [selectedBookId, setSelectedBookId] = useState<string | null>(null);

  const handleSelectBook = (id: string) => {
    setSelectedBookId(id);
  };

  return (
    <div>
      <h1>BookShare</h1>
      <BookList books={books} onSelectBook={handleSelectBook} />
    </div>
  );
}

export default App;
