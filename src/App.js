import React from 'react';
import AudiobookList from './AudiobookList'
import './App.css';

class App extends React.Component {
  render() {
    return (
      <div className="App">
        <AudiobookList url="https://9w0bfpgtif.execute-api.eu-central-1.amazonaws.com/audiobooks_library_pre_prod"/>
      </div>
    );
  }
}

export default App;
