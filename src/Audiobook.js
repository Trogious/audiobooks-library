import React from 'react'
import './Audiobook.css'

class Audiobook extends React.Component {
  constructor (props) {
    super(props);
    this.state = {
      lengthStr: this.getLengthStr(this.props.length),
      sizeStr: this.getFileSizeStr(this.props.size)
    }
  }

  getFormattedStrInt(num) {
    num = Math.trunc(num);
    return (num > 9) ? `${num}` : `0${num}`;
  }

  getLengthStr(lengthInMs2) {
    let ms = lengthInMs2 % 1000;
    lengthInMs2 = lengthInMs2 / 1000;
    let s = lengthInMs2 % 60;
    lengthInMs2 = lengthInMs2 / 60;
    let m = lengthInMs2 % 60;
    let h = lengthInMs2 / 60;

    if ((ms | s | m | h) > 0) {
      return this.getFormattedStrInt(h) + ':' + this.getFormattedStrInt(m) + ':' + this.getFormattedStrInt(s) + '.' + this.getFormattedStrInt(Math.trunc(ms/10));
    }
    return '0';
  }

  getFileSizeStr(bytes) {
    if (bytes > 0) {
      let factor = Math.floor(Math.log10(bytes) / 3);
      let size = bytes / Math.pow(1024, factor);
      return size.toFixed(2) + ' ' + ((factor < 6) ? ['B', 'K', 'M', 'G', 'T', 'P'][factor] : "");
    }
    return '0';
  }

  render () {
    return (
      <div className="audiobook">
        <div className="prop">{this.props.name}</div>
        <div className="prop">{this.props.filename}</div>
        <div className="prop">{this.state.lengthStr}</div>
        <div className="prop">{this.state.sizeStr}</div>
      </div>
    )
  }
}

export default Audiobook;
