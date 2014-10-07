ifdef REGENERATE_PARSERS

regenerate: clean BoolExpLexer.cpp_shipped

clean:
	rm -rf location.hh stack.hh position.hh BoolExpParser.hh
	rm -rf *_shipped

.PRECIOUS: location.hh stack.hh position.hh BoolExpParser.hh
.PRECIOUS: BoolExpParser.cpp_shipped BoolExpLexer.cpp_shipped

%.cpp_shipped: %.l BoolExpParser.cpp_shipped
	flex -o $@ $<

%.cpp_shipped: %.y
	bison -o $@ --defines=BoolExpParser.hh $<

endif
