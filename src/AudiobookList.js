import React from 'react'
import Audiobook from './Audiobook'
import './AudiobookList.css'

class AudiobookList extends React.Component {
  constructor (props) {
    // console.log("constructor");
    super(props);
    this.state = { audiobooks: null }
  }

  componentWillMount() {
    // console.log("componentWillMount");
  }

  componentWillReceiveProps(nextProps) {
    // console.log("componentWillReceiveProps");
  }

  componentWillUpdate(nextProps, nextState) {
    // console.log("componentWillUpdate");
  }

  componentDidMount() {
    // console.log("componentDidMount");
    fetch(this.props.url).then(r => r.json())
      .then(data => {
          this.setState({ audiobooks: data });
        })
      .catch(e => console.error(e));
  }

  render () {
    // console.log("render");
    return (
      <div className="audiobooks">
        {this.state.audiobooks === null ? "" : this.state.audiobooks.map((a, i) => <Audiobook {...a} key={i}/>)}
      </div>
    )
  }
}

export default AudiobookList;
